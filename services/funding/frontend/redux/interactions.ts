import {projectsSlice, userSlice, web3Slice} from "@/redux/reducers";
import {AppDispatch} from "@/redux/store";
import {Web3} from 'web3';
import ProjectContract from '../../ethereum/artifacts/contracts/Project.sol/Project.json'
import CrowdfundingPlatformContract from '../../ethereum/artifacts/contracts/CrowdfundingPlatform.sol/CrowdfundingPlatform.json'

export async function loadWeb3(dispatch: AppDispatch) {
    const web3 = new Web3(window.ethereum);
    dispatch(web3Slice.actions.connect(web3));
    return web3;
}

export async function loadUserAddress(web3: Web3, dispatch: AppDispatch) {
    const accounts = await web3.eth.getAccounts();

    if (accounts) {
        dispatch(web3Slice.actions.setUserAddress(accounts[0]));
    }

    return accounts;
}

export async function loadProjects(dispatch: AppDispatch) {
    const response = await fetch("/api/projects/");
    const json = await response.json();

    if (json.projects) {
        dispatch(projectsSlice.actions.set(json.projects));
    }
}

export async function loadProject(projectId: number) {
    const response = await fetch(`/api/projects/${projectId}`);
    const json = await response.json();

    return json.project;
}

export async function loadPlatformAddress(dispatch: AppDispatch) {
    const response = await fetch("/api/");
    const json = await response.json();

    if (json.address) {
        dispatch(web3Slice.actions.setPlatformAddress(json.address));
    }
}

export async function loadUser(dispatch: AppDispatch) {
    const response = await fetch("/api/users/");
    if (!response.ok)
        return;
    const json = await response.json();

    const {user_id, address} = json;
    dispatch(userSlice.actions.authenticate({userId: user_id, address}));
}

export async function authenticate(address: string, password: string, dispatch: AppDispatch) {
    let request = new Request(
        "/api/users/",
        <RequestInit>{method: "POST", body: JSON.stringify({address, password}), headers: {"Content-Type": "application/json"}}
    );
    try {
        const response = await fetch(request);
        const json = await response.json();
        if (!json.user_id)
            return false;

        const {user_id, address} = json;
        dispatch(userSlice.actions.authenticate({userId: user_id, address}));
        return true;
    } catch (e) {
        return false;
    }
}

export async function logout(dispatch: AppDispatch) {
    let request = new Request(
        "/api/users/logout/",
        <RequestInit>{method: "POST"}
    );
    await fetch(request);
    dispatch(userSlice.actions.logout());
}

export async function createProjectContract(web3: Web3, userAddress: string, platformAddress: string, title: string) {
    const contract = new web3.eth.Contract(CrowdfundingPlatformContract.abi, platformAddress);
    // @ts-ignore
    const receipt = await contract.methods.createProject(title).send({from: userAddress});

    const log = receipt.logs[0];
    if (!log.data || !log.topics)
        return null;

    const parsedLog = web3.eth.abi.decodeLog(
        CrowdfundingPlatformContract.abi[0].inputs,
        log.data,
        log.topics,
    );
    return parsedLog._address as string;
}

export async function createProjectInApi(address: string, reward: string, dispatch: AppDispatch) {
    let request = new Request(
        "/api/projects/",
        <RequestInit>{method: "POST", body: JSON.stringify({address, reward}), headers: {"Content-Type": "application/json"}}
    );
    const response = await fetch(request);
    const json = await response.json();

    dispatch(projectsSlice.actions.add(json.project));
}

export async function donate(web3: Web3, userAddress: string, projectAddress: string, amount: string) {
    const contract = new web3.eth.Contract(ProjectContract.abi, projectAddress);
    await contract.methods.donate().send({from: userAddress, value: amount});
}

export async function withdraw(web3: Web3, userAddress: string, projectAddress: string, amount: string) {
    const contract = new web3.eth.Contract(ProjectContract.abi, projectAddress);
    // @ts-ignore
    await contract.methods.withdraw(amount).send({from: userAddress});
}

export async function getReward(projectId: number) {
    const response = await fetch(`/api/projects/${projectId}/reward/`);
    const json = await response.json();

    return json.reward;
}