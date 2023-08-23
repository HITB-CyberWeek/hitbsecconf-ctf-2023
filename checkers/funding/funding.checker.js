#!/usr/bin/env node

import {argv} from "node:process";
import {readFileSync} from "fs";
import crypto from "crypto";
import {faker} from '@faker-js/faker';
import consoleStamp from "console-stamp";
import {Web3} from "web3"
import {fetch as fetchWithCookies, CookieJar} from "node-fetch-cookies";
import {passwordSalt, ethereum as ethereumConfig} from "./config.js"

consoleStamp(console, {format: ':date(HH:MM:ss.l)', include: ['error']});

// Copy contract ABIs from the service folder:
// cp ../../services/funding/ethereum/artifacts/contracts/CrowdfundingPlatform.sol/CrowdfundingPlatform.json ../../services/funding/ethereum/artifacts/contracts/Project.sol/Project.json contracts/
const CrowdfundingPlatformContract = JSON.parse(readFileSync(new URL('./contracts/CrowdfundingPlatform.json', import.meta.url)));
const ProjectContract = JSON.parse(readFileSync(new URL('./contracts/Project.json', import.meta.url)));

Array.prototype.random = function () {
    return this[Math.floor((Math.random() * this.length))];
}

const web3 = new Web3(ethereumConfig.node);


const STATUS_OK = 101;
const STATUS_CORRUPT = 102;
const STATUS_MUMBLE = 103;
const STATUS_DOWN = 104;
const STATUS_CHECKER_ERROR = 110;

function exitWithStatus(status, private_message = null, public_message = null) {
    if (public_message)
        console.log(public_message);
    if (private_message)
        console.error(private_message);
    process.exit(status);
}

function _getUrlPrefix(host) {
    if (process.env.DIRECT_CONNECT)
        return `http://${host}/api`;
    return `https://${host}/api`;
}

async function _sendRequest(url, options, cookieJar = null, errorStatus = STATUS_MUMBLE) {
    console.error(`Sending ${options.method || "GET"} request to ${url}`);

    cookieJar = cookieJar || new CookieJar("");

    let response;
    try {
        response = await fetchWithCookies(cookieJar, url, options);
    } catch (e) {
        exitWithStatus(STATUS_DOWN, `Can not receive response from ${url}: ${e}`, `Can not receive response from ${url}`);
    }
    if (response.status == 502) { // 502 means Bad Gateway from the proxy
        exitWithStatus(
            STATUS_DOWN,
            `Received unexpected HTTP status ${response.status} on ${response.url}: ${await response.text()}`,
            `Can not request ${response.url}`
        )
    }
    if (response.status >= 400) {
        exitWithStatus(
            errorStatus,
            `Received unexpected HTTP status ${response.status} on ${response.url}: ${await response.text()}`,
            `Unexpected HTTP status ${response.status} on ${response.url}`
        );
    }

    try {
        return await response.json();
    } catch (e) {
        exitWithStatus(
            errorStatus,
            `Receive invalid JSON on ${response.url}: ${e.message ? e.message : e}`,
            `Receive invalid JSON on ${response.url}`,
        )
    }
}

async function getJSON(url, cookieJar = null, errorStatus = STATUS_MUMBLE) {
    return await _sendRequest(url, {credentials: "same-origin"}, cookieJar, errorStatus);
}

async function postJSON(url, data, cookieJar = null, errorStatus = STATUS_MUMBLE) {
    return await _sendRequest(
        url,
        {
            method: "POST",
            body: JSON.stringify(data),
            headers: {"Content-Type": "application/json"},
            credentials: "same-origin"
        },
        cookieJar,
        errorStatus,
    );
}

async function getPlatformAddress(url) {
    const address = (await getJSON(url + "/")).address;
    console.error(`Found CrowdfundingPlatform Address: ${address}`);
    return address;
}

function getRandomAccount(teamId, except = null) {
    if (except != null && ethereumConfig.accounts.length <= 1)
        exitWithStatus(STATUS_CHECKER_ERROR, `You must specify more than 1 account in config.js`)

    let teamAccounts = [ethereumConfig.accounts[(teamId - 1) * 2], ethereumConfig.accounts[(teamId - 1) * 2 + 1]]
    console.error(`Team accounts: ${teamAccounts.map(a => a.address)}`);

    let result;
    do {
        result = teamAccounts.random();
    } while (except != null && result.address === except);
    return result;
}

function findAccountByAddress(address) {
    const account = ethereumConfig.accounts.find(account => account.address == address);
    if (!account)
        throw Error(`Can not find ${address} in config.js`);
    return account;
}

async function makeContractCall(call, contractAddress, sender, value=null) {
    let lastException;
    for (let t = 0; t < 3; t++) {
        try {
            const gasPrice = await web3.eth.getGasPrice();
            const gasEstimate = await call.estimateGas({ from: sender.address, value });
            const tx = await web3.eth.accounts.signTransaction({data: call.encodeABI(), to: contractAddress, from: sender.address, gas: gasEstimate, gasPrice, gasEstimate, value}, sender.privateKey);
            return await web3.eth.sendSignedTransaction(tx.rawTransaction);
        } catch (e) {
            console.error(`Can not make transaction: ${e}. I will try one more time (it was try #${t + 1}/3)`);
            lastException = e;
        }
    }
    throw lastException;
}

async function createNewProjectContract(url, platformAddress, title) {
    const platform = new web3.eth.Contract(CrowdfundingPlatformContract.abi, platformAddress);

    let canNotCreateContractMessage = (
        `Failed to create a new project in the blockchain via calling createProject(<title>). ` +
        `Check your CrowdfundingPlatform contract located at ${platformAddress}`
    );

    let account = getRandomAccount(getTeamIdByUrl(url));

    console.error(`Calling CrowdfundingPlatform.createProject("${title}") at address ${platformAddress} using ${account.address}`)
    let receipt;
    try {
        receipt = await makeContractCall(platform.methods.createProject(title), platformAddress, account);
    } catch (e) {
        console.error(e)
        exitWithStatus(
            STATUS_MUMBLE,
            `Failed to create a new project: ${e.message ? e.message : e}`,
            canNotCreateContractMessage
        );
    }

    const log = receipt.logs[0];
    if (!log || !log.data || !log.topics) {
        console.error(receipt);
        exitWithStatus(
            STATUS_MUMBLE,
            `Failed to create a new project: empty logs`,
            canNotCreateContractMessage
        );
    }

    const parsedLog = web3.eth.abi.decodeLog(CrowdfundingPlatformContract.abi[0].inputs, log.data, log.topics);

    if (!parsedLog._address) {
        exitWithStatus(
            STATUS_MUMBLE,
            `Failed to find an address of freshly created contract in logs`,
            canNotCreateContractMessage
        );
    }

    console.error(`Found address of freshly created Project Contract: ${parsedLog._address}`)
    return parsedLog._address;
}

async function createProject(url, reward) {
    const platformAddress = await getPlatformAddress(url);

    const projectTitle = faker.commerce.productName();
    console.error(`Creating project with title "${projectTitle}" and reward "${reward}" at ${url}`);
    const projectAddress = await createNewProjectContract(url, platformAddress, projectTitle);
    const result = await postJSON(`${url}/projects`, {address: projectAddress, reward: reward});
    if (!result || !result.project || !result.project.id || !result.project.owner ||
        result.project.address !== projectAddress || result.project.title !== projectTitle)
        exitWithStatus(STATUS_MUMBLE, `Invalid response from POST request to ${url}/projects: ${JSON.stringify(result)}`, `Invalid response from POST request to ${url}/projects`);

    console.error(`Created project ${result.project.id}`);

    return result.project;
}

async function donate(project, account) {
    const projectContract = new web3.eth.Contract(ProjectContract.abi, project.address);
    let canNotDonateMessage = (
        `Failed to donate to the project in the blockchain via calling donate(). ` +
        `Check your Project contract located at ${project.address}`
    );

    console.error(`Calling Project.donate() at address ${project.address} using ${account.address}`);
    let receipt;
    try {
        receipt = await makeContractCall(projectContract.methods.donate(), project.address, account, web3.utils.toWei(0.0001, "ether"));
    } catch (e) {
        console.error(e);
        exitWithStatus(
            STATUS_MUMBLE,
            `Failed to donate to a project: ${e.message ? e.message : e}`,
            canNotDonateMessage
        );
    }

    return receipt.blockNumber;
}

async function withdraw(project) {
    const projectContract = new web3.eth.Contract(ProjectContract.abi, project.address);
    let canNotDonateMessage = (
        `Failed to donate to the project in the blockchain via calling donate(). ` +
        `Check your Project contract located at ${project.address}`
    );

    let receipt;
    try {
        console.error(`Calling Project.getTotalDonations() at address ${project.address}`);
        const totalDonations = await projectContract.methods.getTotalDonations().call();
        console.error(`Calling Project.withdraw(${totalDonations}) at address ${project.address} using ${project.owner}`);
        receipt = await makeContractCall(projectContract.methods.withdraw(totalDonations), project.address, findAccountByAddress(project.owner));
    } catch (e) {
        console.error(e);
        exitWithStatus(
            STATUS_MUMBLE,
            `Failed to donate to a project: ${e.message ? e.message : e}`,
            canNotDonateMessage
        );
    }

    return receipt.blockNumber;
}

async function createUserOrLogin(url, address) {
    const password = crypto.createHash("md5").update(passwordSalt + url + address + passwordSalt).digest("hex");
    console.error(`Trying to authenticate as ${address} with password ${password}`);

    const cookieJar = new CookieJar();
    const response = await postJSON(`${url}/users/`, {address: address, password: password}, cookieJar);
    if (!response.user_id)
        exitWithStatus(STATUS_CORRUPT, `Can not find "user_id" field in ${response}`, `Invalid response after authentication`);
    console.error(`User id: ${response.user_id}`);
    return cookieJar;
}

function _generateRandomString(length) {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return result;
}

function getTeamIdByUrl(url) {
    // Suppose that url contains something like 10.60.23.5, where 23 is a team number
    let matches = url.match(/\d+.(\d+).(\d+).\d+/);
    if (matches) {
        return (parseInt(matches[1]) - 60) * 256 + parseInt(matches[2]);
    } else {
        // If url is not an IP address, then probable it's a domain name like funding.team23.<domain>
        matches = url.match(/\.team(\d+)\./);
        if (!matches) {
            return null;
        }
        return parseInt(matches[1]);
    }
}

function _generateFakeFlag(url) {
    const randomSuffix = _generateRandomString(32);

    let teamId = getTeamIdByUrl(url);
    if (teamId == null)
        return randomSuffix;

    return "TEAM" + teamId.toString().padStart(3, "0") + "_" + randomSuffix
}

async function info() {
    console.log("vulns: 1");
    console.log("public_flag_description: Flag ID is the project's ID, flag is a reward for the last baker");
    exitWithStatus(STATUS_OK);
}

async function check(url) {
    await getPlatformAddress(url);
    exitWithStatus(STATUS_OK);
}

async function put(url, _flag_id, flag) {
    const fakeProjectReward = _generateFakeFlag(url);

    // Shuffle creating real and fake projects
    const fakeFirst = Math.floor(Math.random() * 2) < 1;
    let fakeProject;
    if (fakeFirst)
        fakeProject = await createProject(url, fakeProjectReward);
    const project = await createProject(url, flag);
    if (!fakeFirst)
        fakeProject = await createProject(url, fakeProjectReward);

    const flag_id = JSON.stringify({public_flag_id: project.id, project, fakeProject, fakeProjectReward});
    exitWithStatus(STATUS_OK, null, flag_id);
}

async function getFlagForProject(url, project, flag) {
    const account = getRandomAccount(getTeamIdByUrl(url), project.owner);
    const cookieJar = await createUserOrLogin(url, account.address);

    await donate(project, account);
    const blockNumber = await withdraw(project)

    let updatedProject;
    let retry = 0;
    do {
        if (retry)
            await new Promise(r => setTimeout(r, 1000 * retry));
        updatedProject = (await getJSON(`${url}/projects/${project.id}`, null, STATUS_CORRUPT)).project;
        retry++;
    } while (retry < 3 && (!updatedProject || !updatedProject.isFinished || updatedProject.lastBaker !== account.address))

    if (!updatedProject || !updatedProject.isFinished || updatedProject.lastBaker !== account.address)
        exitWithStatus(
            STATUS_CORRUPT,
            `Project has not been updated in the service: ${JSON.stringify(updatedProject)}. Should be isFinished = true, lastBaker = ${account.address}`,
            `Can not find my donation in your service`,
        );

    const reward = (await getJSON(`${url}/projects/${project.id}/reward/${blockNumber}`, cookieJar, STATUS_CORRUPT)).reward;
    if (reward !== flag)
        exitWithStatus(STATUS_CORRUPT, `Received wrong reward from the service: ${reward} instead of ${flag}`, `Can not get reward as the last baker`)

    console.error(`Found correct reward "${reward}"`);
}

async function get(url, flag_id, flag) {
    const {project, fakeProject, fakeProjectReward} = JSON.parse(flag_id);

    await getFlagForProject(url, fakeProject, fakeProjectReward);

    exitWithStatus(STATUS_OK);
}

async function main() {
    if (argv.length < 3) {
        exitWithStatus(STATUS_CHECKER_ERROR, `No arguments passed. Usage: ${argv.length[1]} <info|check|put|get> ...`);
    }
    let url;
    switch (argv[2]) {
        case "info":
            return await info();
        case "check":
            url = _getUrlPrefix(argv[3]);
            return await check(url);
        case "put":
            url = _getUrlPrefix(argv[3]);
            return await put(url, argv[4], argv[5]);
        case "get":
            url = _getUrlPrefix(argv[3]);
            return await get(url, argv[4], argv[5]);
        default:
            exitWithStatus(STATUS_CHECKER_ERROR, `Unknown command: ${argv[2]}`);
    }
}


main().catch(e => exitWithStatus(STATUS_CHECKER_ERROR, `Error occurred: ${e.message ? e.message : e}\n${e.stack}`));
