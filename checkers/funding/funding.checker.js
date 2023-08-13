#!/usr/bin/env node

import { argv } from "node:process";
import { readFileSync } from "fs";
import crypto from "crypto";
import { faker } from '@faker-js/faker';
import consoleStamp from "console-stamp";
import { Web3 } from "web3"
import {fetch as fetchWithCookies, CookieJar} from "node-fetch-cookies";
import {passwordSalt, ethereum as ethereumConfig} from "./config.js"

consoleStamp(console, {format: ':date(HH:MM:ss.l)', include: ['error']});


// Copy contract ABIs from the service folder:
// cp ../../services/funding/ethereum/artifacts/contracts/CrowdfundingPlatform.sol/CrowdfundingPlatform.json ../../services/funding/ethereum/artifacts/contracts/Project.sol/Project.json contracts/
const CrowdfundingPlatformContract = JSON.parse(readFileSync('./contracts/CrowdfundingPlatform.json'));
const ProjectContract = JSON.parse(readFileSync('./contracts/Project.json'));

Array.prototype.random = function () {
    return this[Math.floor((Math.random()*this.length))];
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
        return `http://${host}:3001`;
    return `https://${host}`;
}

async function _sendRequest(url, options, cookieJar = null, error_status = STATUS_MUMBLE) {
    console.error(`Sending ${options.method || "GET"} request to ${url}`);

    cookieJar = cookieJar || new CookieJar("");

    let response;
    try {
        response = await fetchWithCookies(cookieJar, url, options);
    } catch (e) {
        exitWithStatus(STATUS_DOWN, `Can not receive response from ${url}: ${e}`, `Can not receive response from ${url}`);
    }
    if (response.status >= 400) {
        exitWithStatus(
            error_status,
            `Received unexpected HTTP status ${response.status} on ${response.url}: ${await response.text()}`,
            `Unexpected HTTP status ${response.status} on ${response.url}`
        );
    }

    try {
        return await response.json();
    } catch (e) {
        exitWithStatus(
            error_status,
            `Receive invalid JSON on ${response.url}: ${e.message ? e.message : e}`,
            `Receive invalid JSON on ${response.url}`,
        )
    }
}

async function getJSON(url, cookieJar = null) {
    return await _sendRequest(url, {credentials: "same-origin"}, cookieJar);
}

async function postJSON(url, data, cookieJar = null) {
    return await _sendRequest(
        url,
        {
            method: "POST",
            body: JSON.stringify(data),
            headers: {"Content-Type": "application/json"},
            credentials: "same-origin"
        },
        cookieJar,
    );
}

async function getPlatformAddress(url) {
    const address = (await getJSON(url)).address;
    console.error(`Found CrowdfundingPlatform Address: ${address}`);
    return address;
}

function getRandomAccount(except = null) {
    if (except != null && ethereumConfig.accounts.length <= 1)
        exitWithStatus(STATUS_CHECKER_ERROR, `You must specify more than 1 account in config.js`)

    let result;
    do {
        result = ethereumConfig.accounts.random();
    } while (except != null && result.address === except);
    return result;
}

async function createNewProjectContract(platformAddress, title) {
    const platform = new web3.eth.Contract(CrowdfundingPlatformContract.abi, platformAddress);

    let canNotCreateContractMessage = (
        `Failed to create a new project in the blockchain via calling createProject(<title>). ` +
        `Check your CrowdfundingPlatform contract located at ${platformAddress}`
    );

    let account = getRandomAccount();

    console.error(`Calling CrowdfundingPlatform.createProject("${title}") at address ${platformAddress} using ${account.address}`)
    let receipt;
    try {
        receipt = await platform.methods.createProject(title).send({from: account.address});
    } catch (e) {
        exitWithStatus(
            STATUS_MUMBLE,
            `Failed to create a new project: ${e.message ? e.message : e}`,
            canNotCreateContractMessage
        );
    }

    const log = receipt.logs[0];
    if (!log.data || !log.topics)
        exitWithStatus(
            STATUS_MUMBLE,
            `Failed to create a new project: empty logs`,
            canNotCreateContractMessage
        );

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

async function createProject(url, award) {
    const platformAddress = await getPlatformAddress(url);

    const projectTitle = faker.commerce.productName();
    console.error(`Creating project with title "${projectTitle}" and award "${award}" at ${url}`);
    const projectAddress = await createNewProjectContract(platformAddress, projectTitle);
    const result = await postJSON(`${url}/projects`, {address: projectAddress, award: award});
    if (!result || !result.project || !result.project.id || !result.project.owner ||
        result.project.address !== projectAddress || result.project.title !== projectTitle)
        exitWithStatus(STATUS_MUMBLE, `Invalid response from POST request to ${url}/projects: ${result}`, `Invalid response from POST request to ${url}/projects`);

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
        receipt = await projectContract.methods.donate().send({from: account.address, value: web3.utils.toWei(0.05, "ether")});
    } catch (e) {
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
        receipt = await projectContract.methods.withdraw(totalDonations).send({from: project.owner});
    } catch (e) {
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

function _generateFakeFlag(url) {
    // Suppose that url contains something like 10.60.23.5, where 23 is a team number
    const matches = url.match(/\d+.(\d+).(\d+).\d+/);
    const randomSuffix = _generateRandomString(32);
    if (!matches) {
        return randomSuffix;
    }
    const teamId = (parseInt(matches[1]) - 60) * 256 + parseInt(matches[2]);
    return "TEAM" + teamId.toString().padStart(3, "0") + "_" + randomSuffix
}

async function info() {
    console.log("vulns: 1");
    console.log("public_flag_description: Flag ID is the project's ID. Flag is an award for the last baker.");
    exitWithStatus(STATUS_OK);
}

async function check(url) {
    exitWithStatus(STATUS_OK);
}

async function put(url, _flag_id, flag) {
    const fakeProjectAward = _generateFakeFlag(url);
    const fakeProject = await createProject(url, fakeProjectAward);
    const project = await createProject(url, flag);

    const flag_id = JSON.stringify({public_flag_id: project.id, project, fakeProject, fakeProjectAward});
    exitWithStatus(STATUS_OK, null, flag_id);
}

async function getFlagForProject(url, project, flag) {
    const account = getRandomAccount(project.owner);
    const cookieJar = await createUserOrLogin(url, account.address);

    await donate(project, account);
    const blockNumber = await withdraw(project)

    let updatedProject;
    let retry = 0;
    do {
        if (retry)
            await new Promise(r => setTimeout(r, 1000 * retry));
        updatedProject = (await getJSON(`${url}/projects/${project.id}`)).project;
        retry++;
    } while (retry < 3 && (!updatedProject || !updatedProject.isFinished || updatedProject.lastBaker !== account.address))

    if (!updatedProject || !updatedProject.isFinished || updatedProject.lastBaker !== account.address)
        exitWithStatus(
            STATUS_CORRUPT,
            `Project has not been updated in the service: ${JSON.stringify(updatedProject)}. Should be isFinished = true, lastBaker = ${account.address}`,
            `Can not find my donation in your service`,
        );

    const award = (await getJSON(`${url}/projects/${project.id}/award/${blockNumber}`, cookieJar)).award;
    if (award !== flag)
        exitWithStatus(STATUS_CORRUPT, `Received invalid award from the service: ${award} instead of ${flag}`, `Can not get award as the last baker`)

    console.error(`Found correct award "${award}"`);
}

async function get(url, flag_id, flag) {
    const {project, fakeProject, fakeProjectAward} = JSON.parse(flag_id);

    await getFlagForProject(url, fakeProject, fakeProjectAward);

    exitWithStatus(STATUS_OK);
}

async function main(args) {
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