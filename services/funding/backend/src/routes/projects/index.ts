import {FastifyInstance, FastifyPluginAsync} from 'fastify';
import * as ProjectContract from '../../../../ethereum/artifacts/contracts/Project.sol/Project.json'

interface IProjectRequest {
    address: string;
    award: string;
}

interface IGetProjectParams {
    projectId: number;
}

interface IGetAwardParams {
    projectId: number;
    blockNumber: number;
}

async function getProjectInfo<RawServer>(fastify: FastifyInstance, project: {id: number, address: string}) {
    try {
        const contract = new fastify.web3.eth.Contract(ProjectContract.abi, project.address);

        const owner: string = await contract.methods.owner().call();
        const title: string = await contract.methods.title().call();
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
        return {
            id: project.id,
            address: project.address,
            error: e instanceof Error ? e.message : e
        };
    }
}

const projects: FastifyPluginAsync = async function (fastify: FastifyInstance, opts) {
    fastify.post<{ Body: IProjectRequest }>(
        '/', {},
        async (request, reply) => {
            let { address, award } = request.body;
            fastify.assert(address, 400, 'Address can not be empty');
            fastify.assert(award, 400, 'Award can not be empty');

            // TODO: check address format

            const project = await fastify.database.one(
                'INSERT INTO projects (address, award) VALUES ($1, $2) RETURNING id, address',
                [address, award]
            );
            reply.code(201).send({project: await getProjectInfo(fastify, project)});
        }
    );

    fastify.get(
        '/', {},
        async (request, reply) => {
            const projects = await fastify.database.manyOrNone('SELECT id, address FROM projects ORDER BY id DESC LIMIT 20');
            // TODO: add paging
            const projectDetails = await Promise.all(projects.map(project => getProjectInfo(fastify, project)))
            reply.send({projects: projectDetails});
        }
    );

    fastify.get<{ Params: IGetProjectParams }>(
        '/:projectId(^\\d+)', {},
        async (request, reply) => {
            const { projectId} = request.params;
            const project = await fastify.database.oneOrNone('SELECT address FROM projects WHERE id = $1', [projectId]);
            fastify.assert(project, 404, `Project ${projectId} not found`);

            reply.send({project: await getProjectInfo(fastify, project)});
        }
    );

    fastify.get<{ Params: IGetAwardParams }>(
        '/:projectId(^\\d+)/award/:blockNumber?', {},
        async (request, reply) => {
            fastify.assert(request.session.userId, 401, 'You are not authenticated');
            const user = await fastify.database.one('SELECT address FROM users WHERE id = $1', [request.session.userId]);

            const {projectId, blockNumber} = request.params;
            const project = await fastify.database.oneOrNone('SELECT id, address, award FROM projects WHERE id = $1', [projectId])
            fastify.assert(project, 404, `Project ${projectId} not found`);

            const contract = new fastify.web3.eth.Contract(ProjectContract.abi, project.address);

            const isFinished: boolean = await contract.methods.isFinished().call({}, blockNumber || 'latest')
            fastify.assert(isFinished, 404, `Owner of the contract ${project.address} hasn't withdrawn his money yet`);

            const lastBaker: string = await contract.methods.getLastBaker().call({}, blockNumber || 'latest')
            fastify.assert(
                lastBaker != '0x0000000000000000000000000000000000000000',
                404,
                `Nobody has donated contract ${project.address} yet`
            )

            fastify.assert(
                lastBaker.toLowerCase() == user.address,
                404,
                `Only last baker of the project can receive the award`
            )

            reply.send({award: project.award})
        }
    );
}

export default projects;