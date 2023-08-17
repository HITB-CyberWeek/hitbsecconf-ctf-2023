import { FastifyInstance } from 'fastify'
import fastifyPlugin from 'fastify-plugin'
import fastifyCookie from '@fastify/cookie';
import fastifySession, { SecureSessionPluginOptions } from '@fastify/secure-session';
import * as fs from 'fs';
import * as path from 'path';


export default fastifyPlugin<FastifyInstance>(
    async (fastify, opts, done) => {
        fastify.register(fastifyCookie)
        fastify.register(fastifySession, <SecureSessionPluginOptions>{
            cookieName: 'session',
            key: fs.readFileSync(path.join(__dirname, '..', '.cookie.key')),
            cookie: { path: '/', secure: false },
            expires: 1800000
        });

        done();
    }
)

declare module '@fastify/secure-session' {
    export interface SessionData {
        userId: number;
    }
}
