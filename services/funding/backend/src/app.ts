import { join } from 'path';
import AutoLoad, {AutoloadPluginOptions} from '@fastify/autoload';
import { FastifyPluginAsync, FastifyServerOptions } from 'fastify';

export interface AppOptions extends FastifyServerOptions, Partial<AutoloadPluginOptions> {

}
// Pass --options via CLI arguments in command to enable these options.
export const options: AppOptions = {
    ignoreTrailingSlash: true
}

const app: FastifyPluginAsync<AppOptions> = async (
    fastify,
    opts
) => {
    // This loads all plugins defined in plugins
    // those should be support plugins that are reused
    // through your application
    await fastify.register(AutoLoad, {
        dir: join(__dirname, 'plugins'),
        options: opts
    })

    // This loads all plugins defined in routes
    // define your routes in one of these
    await fastify.register(AutoLoad, {
        dir: join(__dirname, 'routes'),
        options: opts
    })
};


export default app;
