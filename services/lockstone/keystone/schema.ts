import { list } from '@keystone-6/core';
import { allowAll, denyAll } from '@keystone-6/core/access';
import { text, password, timestamp, relationship } from '@keystone-6/core/fields';
import type { Lists } from '.keystone/types';

import { document } from '@keystone-6/fields-document';

const isSameUser = ({ session, item }: { session: SessionData, item: PersonData }) => {
    return session?.data.id === item.id;
  }

export const lists: Lists = {
  User: list({
    access: {
      operation: {
        query: allowAll,
        create: allowAll,
        update: denyAll,
        delete: denyAll,
      },
    },

    fields: {
      login: text({
        validation: { isRequired: true },
        isIndexed: 'unique',
      }),

      flag: text({
        access: {
          read: isSameUser
        },
      }),

      password: password({ validation: { isRequired: true } }),

      createdAt: timestamp({ defaultValue: { kind: 'now' } }),

    },
    ui: {
      labelField: "login",
      description: "Log in to see your flag",
      searchFields: ["login"],
      hideDelete: true,
      listView: {
        initialColumns: ["login", "flag"],
        initialSort: {field: "createdAt", direction: "DESC"}
      },
    },
    graphql: {
      maxTake: 100,
    }
  })
};
