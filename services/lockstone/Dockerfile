FROM ubuntu:23.04

RUN useradd -m -u 10000 lockstone

RUN apt-get update && apt-get install -y nodejs

RUN apt-get install -y npm

COPY --chown=lockstone package.json package-lock.json tsconfig.json schema.graphql schema.prisma keystone.ts /home/lockstone
COPY --chown=lockstone admin /home/lockstone/admin
COPY --chown=lockstone keystone /home/lockstone/keystone
COPY --chown=lockstone migrations /home/lockstone/migrations

WORKDIR /home/lockstone/
RUN su -s /bin/bash -c "npm install" lockstone

COPY --chown=lockstone start.sh /home/lockstone/start.sh

CMD ["./start.sh"]
