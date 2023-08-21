import { FastifyInstance, FastifyPluginAsync } from 'fastify';
import * as ProjectContract from '../../../../ethereum/artifacts/contracts/Project.sol/Project.json'

interface IProjectRequest {
    address: string;
    reward: string;
}

interface IGetProjectParams {
    projectId: number;
}

interface IGetRewardParams {
    projectId: number;
    blockNumber: number;
}

interface ProjectInfo {
    id: number;
    address: string;
    owner?: string;
    title?: string;
    totalDonations?: string;
    lastBaker?: string;
    isFinished?: boolean;
    error?: string;
}

async function getProjectInfo(fastify: FastifyInstance, project: {id: number, address: string}, retry: number = 1): Promise<ProjectInfo> {
    try {
        const contract = new fastify.web3.eth.Contract(ProjectContract.abi, project.address);

        const owner: string = await contract.methods.getOwner().call();
        const title: string = await contract.methods.getTitle().call();
        const totalDonations: number = await contract.methods.getTotalDonations().call();
        const lastBaker: string = await contract.methods.getLastBaker().call();
        const isFinished: boolean = await contract.methods.isFinished().call();

        return {
            id: project.id,
            address: project.address,
            owner,
            title,
            totalDonations: totalDonations.toString(),
            lastBaker,
            isFinished
        };
    } catch (e) {
        if (retry <= 3) { // Probably our node has not synced this block yet? 
            await new Promise(f => setTimeout(f, 1000 * retry));
            return await getProjectInfo(fastify, project, retry + 1);
        }
        return {
            id: project.id,
            address: project.address,
            error: e instanceof Error ? e.message : JSON.stringify(e)
        };
    }
}

const projects: FastifyPluginAsync = async function (fastify: FastifyInstance, opts) {
    fastify.post<{ Body: IProjectRequest }>(
        '/', {},
        async (request, reply) => {
            fastify.assert(request.body, 400, 'Body can not be empty');
            let { address, reward } = request.body;
            fastify.assert(address, 400, 'Address can not be empty');
            fastify.assert(address.startsWith("0x"), 400, 'Address must start with 0x');
            fastify.assert(address.length == 42, 400, 'Address must have 40 hex digits preceding by 0x');
            fastify.assert(reward, 400, 'Reward can not be empty');

            const project = await fastify.database.one(
                'INSERT INTO projects (address, reward) VALUES ($1, $2) RETURNING id, address',
                [address, reward]
            );
            reply.code(201).send({project: await getProjectInfo(fastify, project)});
        }
    );

    fastify.get(
        '/', {},
        async (request, reply) => {
            const projects = await fastify.database.manyOrNone('SELECT id, address FROM projects ORDER BY id DESC LIMIT 10');
            const projectDetails = await Promise.all(projects.map(project => getProjectInfo(fastify, project)));
            reply.send({projects: projectDetails});
        }
    );

    fastify.get<{ Params: IGetProjectParams }>(
        '/:projectId(^\\d+)', {},
        async (request, reply) => {
            const { projectId} = request.params;
            const project = await fastify.database.oneOrNone('SELECT id, address FROM projects WHERE id = $1', [projectId]);
            fastify.assert(project, 404, `Project ${projectId} not found`);

            reply.send({project: await getProjectInfo(fastify, project)});
        }
    );

    fastify.get<{ Params: IGetRewardParams }>(
        '/:projectId(^\\d+)/reward/:blockNumber?', {},
        async (request, reply) => {
            fastify.assert(request.session.userId, 401, 'You are not authenticated');
            const user = await fastify.database.one('SELECT address FROM users WHERE id = $1', [request.session.userId]);

            const {projectId, blockNumber} = request.params;
            const project = await fastify.database.oneOrNone('SELECT id, address, reward FROM projects WHERE id = $1', [projectId]);
            fastify.assert(project, 404, `Project ${projectId} not found`);

            const contract = new fastify.web3.eth.Contract(ProjectContract.abi, project.address);

            const isFinished: boolean = await contract.methods.isFinished().call({}, blockNumber || 'latest');
            fastify.assert(isFinished, 404, `Owner of the contract ${project.address} hasn't withdrawn his money yet`);

            const lastBaker: string = await contract.methods.getLastBaker().call({}, blockNumber || 'latest');
            fastify.assert(
                lastBaker != '0x0000000000000000000000000000000000000000',
                404,
                `Nobody has donated to contract ${project.address} yet`
            );

            fastify.assert(
                lastBaker.toLowerCase() == user.address,
                404,
                `Only last baker of the project can receive the reward`
            );

            reply.send({reward: project.reward});
        }
    );
}

export default projects;
