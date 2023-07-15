#!/bin/bash

set -ex

# Wait while Cloud copies network config to the router
while ! ls /etc/openvpn/game_network_team*.conf
do
  echo "Can not find file /etc/openvpn/game_network_team*.conf, waiting..."
  sleep 1
done

if [ ! -f /home/router/do_api_token ]
then
  echo "[ERROR] Expected DO API token in ~/do_api_token, but file not found"
  exit 1
fi

export CERTIFICATES_FOLDER=/home/router/certificates
export DO_API_TOKEN="$(cat /home/router/do_api_token)"

# I didn't find a better way to find the team id: just look on OpenVPN config,
# if it's called /etc/openvpn/game_network_team152.conf, then it's a router of Team 152.
team_id=$(find /etc/openvpn/game_network_team*.conf | sed -e s/[^0-9]//g)

cd "$(dirname "$0")"/../

python3 deploy_proxies.py --local --team-id "$team_id" --prepare-only
for deploy_yaml in configs/*/deploy.yaml
do
  python3 deploy_proxies.py --local --team-id "$team_id" --skip-preparation "$deploy_yaml"
done