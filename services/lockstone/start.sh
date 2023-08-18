#!/bin/sh

chown lockstone:lockstone -R /home/lockstone/

su -s /bin/bash -c "npm install" lockstone

#su -s /bin/bash -c "npm run migrate" lockstone

su -s /bin/bash -c "npm run build" lockstone

su -s /bin/bash -c "npm run migrate_apply" lockstone 
exec su -s /bin/bash -c "npm run start --with-migrations" lockstone
