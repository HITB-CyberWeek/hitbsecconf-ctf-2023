#!/bin/sh

chown lockstone:lockstone /home/lockstone/keystone.db

export NODE_ENV=production

su -s /bin/bash -c "npm run build" lockstone
su -s /bin/bash -c "npm run migrate_apply" lockstone 
exec su -s /bin/bash -c "npm run start --with-migrations" lockstone
