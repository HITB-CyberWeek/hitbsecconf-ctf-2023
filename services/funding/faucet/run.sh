#!/bin/bash

set -ex

mkdir -p ssl_private

if [ ! -e ssl_private/dhparam.pem ]
then
    openssl dhparam -dsaparam -out ssl_private/dhparam.pem 4096
fi
docker compose build --pull

if [ ! -e /etc/letsencrypt/archive/eth.ctf.hitb.org/privkey1.pem ]
then
    echo "/etc/letsencrypt/archive/eth.ctf.hitb.org/privkey1.pem doesn't exist!"
    exit 1
fi

docker compose down
docker compose up -d