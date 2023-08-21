import { FastifyInstance, FastifyPluginAsync } from 'fastify';
import * as bcrypt from 'bcrypt'

interface IUserRequest {
    address: string;
    password: string;
}

function validateUserRequest(fastify: FastifyInstance, request: IUserRequest): IUserRequest {
    fastify.assert(request, 400, 'Body can not be empty');

    const password = request.password;
    fastify.assert(password, 400, 'Password can not be empty');

    fastify.assert(request.address, 400, 'Address can not be empty');
    const address = request.address.toLowerCase();
    fastify.assert(request.address.startsWith("0x"), 400, 'Address must start with 0x');
    fastify.assert(request.address.length == 42, 400, 'Address must have 40 hex digits preceding by 0x');

    return {address, password};
}

const users: FastifyPluginAsync = async function (fastify: FastifyInstance, opts) {
    fastify.post<{ Body: IUserRequest }>(
        '/', {},
        async (request, reply) => {
            let { address, password } = validateUserRequest(fastify, request.body);

            let user = await fastify.database.oneOrNone('SELECT * FROM users WHERE address = $1', [address]);
            if (user) {
                fastify.assert(await bcrypt.compare(password, user.password_hash), 401, 'Wrong password');

                request.session.userId = user.id;
                reply.send({user_id: user.id, address});
                return;
            }

            const password_hash = await bcrypt.hash(password, 8);

            try {
                user = await fastify.database.one(
                    'INSERT INTO users (address, password_hash) VALUES ($1, $2) RETURNING id',
                    [address, password_hash]
                );

                request.session.userId = user.id;
                reply.code(201).send({user_id: user.id, address});
            } catch (e) {
                reply.conflict('This address is already registered');
            }
        }
    );

    fastify.get(
        '/', {},
        async (request, reply) => {
            fastify.assert(request.session.userId, 401, 'You are not authenticated');

            const user = await fastify.database.oneOrNone('SELECT address FROM users WHERE id = $1', [request.session.userId]);
            fastify.assert(user, 404, 'Invalid cookie, please authenticate again');

            reply.send({user_id: request.session.userId, address: user.address});
        }
    )

    fastify.post(
        '/logout/', {},
        async (request, reply) => {
            fastify.assert(request.session.userId, 401, 'You are not authenticated');

            request.session.delete();
            reply.send({message: 'Successfully log out'});
        }
    )
}

export default users;