import { FastifyPluginAsync } from 'fastify'

const root: FastifyPluginAsync = async (fastify, opts): Promise<void> => {
    fastify.get('/', async function (request, reply) {
        // TODO: get address from env
        return {
            address: "0x620A5E1575e4f2FAaD5bBA260504ce2aCD2dB23A"
        }
    })
}

export default root;
