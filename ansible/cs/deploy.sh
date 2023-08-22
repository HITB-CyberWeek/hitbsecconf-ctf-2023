#!/bin/bash

ansible-playbook -D ../../checksystem/ansible/cs-deploy.yml
ansible-playbook -D ../../checksystem/ansible/cs-init.yml
ansible-playbook -D ../../checksystem/ansible/cs-start.yml
