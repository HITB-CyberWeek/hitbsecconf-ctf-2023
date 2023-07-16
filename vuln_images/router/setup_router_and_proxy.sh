#!/bin/bash

set -ex

# Set up the router: https://github.com/HackerDom/ctf-cloud/tree/master/cloud#deploy-router-host

# Wait for apt-get lock
while ps -opid= -C apt-get > /dev/null; do sleep 1; done

# These lines allow to install iptables-persistent without manual input
echo iptables-persistent iptables-persistent/autosave_v4 boolean true | sudo debconf-set-selections
echo iptables-persistent iptables-persistent/autosave_v6 boolean true | sudo debconf-set-selections

apt-get install -y -q -o DPkg::Lock::Timeout=-1 openvpn iptables-persistent net-tools
# Masquerading for outgoing internet traffic
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
# Docker on a router needs this rule: https://docs.docker.com/network/packet-filtering-firewalls/#docker-on-a-router
iptables -I DOCKER-USER -j ACCEPT
iptables-save > /etc/iptables/rules.v4

echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf
echo 'net.nf_conntrack_max=524288' >> /etc/sysctl.conf
echo 'net.netfilter.nf_conntrack_max=524288' >> /etc/sysctl.conf
sysctl -p

sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
systemctl restart sshd

# Python is required for deploying proxies
apt-get install -y -q python3

# Ubuntu 20.04 has problems with PyOpenSSL installed via python3-pip: https://stackoverflow.com/questions/73830524/attributeerror-module-lib-has-no-attribute-x509-v-flag-cb-issuer-check
wget --quiet https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py

# Install requirements
pip3 install -Ur "$(dirname "$0")/../requirements.txt"

# Do some preparations to speed up proxies deploying later
apt-get install -y nginx openssl jq
openssl dhparam -dsaparam -out /etc/nginx/dhparam.pem 4096
