#!/bin/bash

n=$1
HOST="${HOST:-localhost}"
CHECKER_DIRECT_CONNECT="${CHECKER_DIRECT_CONNECT:-1}"
export CHECKER_DIRECT_CONNECT

function check_verdict () {
    verdict=$?
    if [ $verdict -ne 0 ]
    then
        echo "ERROR:Bad retcode:$verdict"
        exit 200
    fi
}

for i in $(seq 1 $n)
do
    echo "RUN:$i"
    ./hack_hack.py $HOST
    check_verdict

done
