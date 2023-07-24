import { config } from '@keystone-6/core';
import { lists } from './keystone/schema';
import type { Context } from '.keystone/types';

import { withAuth, session } from './keystone/auth';

export default withAuth(
  config({
    db: {
      provider: 'postgresql',
      url: `postgres://postgres:postgres@localhost/lockstone?host=/var/run/postgresql`,
    },
    lists,
    session,
    ui: {
      // isDisabled: true,
      isAccessAllowed: (context) =>  true,
    }
  })
);
