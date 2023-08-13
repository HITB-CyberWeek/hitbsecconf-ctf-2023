import { FastifyPluginAsync } from 'fastify'
import configuration from "../config";

const index: FastifyPluginAsync = async (fastify, opts): Promise<void> => {
    fastify.get('/', async function (request, reply) {
        return {
            address: configuration.crowdfundingPlatformAddress
        };
    })
}

export default index;
