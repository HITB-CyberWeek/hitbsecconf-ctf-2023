import { FastifyInstance } from 'fastify'
import fastifyPlugin from 'fastify-plugin'
import Web3 from 'web3';
import configuration from "../config";

export default fastifyPlugin<FastifyInstance>(
    async (fastify, opts, done) => {
        const web3 = new Web3(configuration.ethereumNodeUrl);
        fastify.decorate('web3', web3);
        done();
    }
)

declare module 'fastify' {
    export interface FastifyInstance {
        web3: Web3
    }
}