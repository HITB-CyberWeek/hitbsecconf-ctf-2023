import { FastifyInstance } from 'fastify'
import fastifyPlugin from 'fastify-plugin'
import * as pgPromise from 'pg-promise'
import configuration from '../config'

const pgp = pgPromise({})

const createTableQueries = [
    `
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    address VARCHAR(42) NOT NULL UNIQUE,
    password_hash VARCHAR(100) NOT NULL
)
`,`
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    address VARCHAR(42) NOT NULL,
    reward TEXT NOT NULL
)
`
]

export default fastifyPlugin<FastifyInstance>(
    async (fastify, opts, done) => {
        const database = pgp(configuration.databaseUrl);

        createTableQueries.forEach(database.none);

        fastify.decorate('database', database)
        done();
    }
)

declare module 'fastify' {
    export interface FastifyInstance {
        database: pgPromise.IDatabase<{}>
    }
}