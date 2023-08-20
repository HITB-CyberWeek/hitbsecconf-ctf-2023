import { config } from '@keystone-6/core';
import { lists } from './keystone/schema';
import type { Context } from '.keystone/types';

import { withAuth, session } from './keystone/auth';

export default withAuth(
  config({
    db: {
      provider: 'sqlite',
      url: `file:${process.cwd()}/keystone.db`,
    },
    lists,
    session,
    ui: {
      isAccessAllowed: (context) =>  true,
    }
  })
);
