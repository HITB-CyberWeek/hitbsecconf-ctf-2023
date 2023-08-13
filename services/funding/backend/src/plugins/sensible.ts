import fastifyPlugin from 'fastify-plugin'
import sensible, { SensibleOptions } from '@fastify/sensible'

/**
 * This plugins adds some utilities to handle http errors
 * @see https://github.com/fastify/fastify-sensible
 */
export default fastifyPlugin<SensibleOptions>(async (fastify) => {
    fastify.register(sensible);
})
