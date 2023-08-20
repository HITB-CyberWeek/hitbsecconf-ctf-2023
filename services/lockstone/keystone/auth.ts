import { randomBytes } from 'crypto';
import { createAuth } from '@keystone-6/auth';

import { statelessSessions } from '@keystone-6/core/session';

let sessionSecret = randomBytes(32).toString('hex');

// set this to some secret sting persist session on restarts
//sessionSecret = "Le26P7xCD8hEwFU8of4eFR2rjukvCfYG"

const { withAuth } = createAuth({
  listKey: 'User',
  identityField: 'login',
  sessionData: 'id',
  secretField: 'password',
});

const sessionMaxAge = 60 * 60 * 24 * 30;

const session = statelessSessions({
  maxAge: sessionMaxAge,
  secret: sessionSecret!,
});

export { withAuth, session };
