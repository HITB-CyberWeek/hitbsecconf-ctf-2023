import {FastifyPluginAsync} from "fastify";

const health: FastifyPluginAsync = async function (fastify, opts) {
    fastify.get('/', {
        schema: {
            description: 'This is an endpoint for application health check',
            tags: ['health'],
            response: {
                200: {
                    description: 'Success Response',
                    type: 'object',
                    properties: {
                        result: { type: 'integer' },
                        message: { type: 'string' }
                    }
                }
            }
        }
    }, async (request, reply) => {
        const result = await fastify.database.one("SELECT 1 AS result");
        reply.send({ result: result.result, message: "The Application is Up and Running" })
    })
}

export default health;