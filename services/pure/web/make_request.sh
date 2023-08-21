#!/bin/bash

curl -k --cert ../certs/client.crt --key ../certs/client.key --cacert ../certs/ca.crt -XGET 'https://localhost/'
