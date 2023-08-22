#!/bin/bash

n=$1
HOST="${HOST:-localhost}"
CHECKER_DIRECT_CONNECT="${CHECKER_DIRECT_CONNECT:-1}"
export CHECKER_DIRECT_CONNECT


function random_string () {
    chars=123qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM
    rand_string=
    for i in {1..20} ; do
        rand_string="${rand_string}${chars:RANDOM%${#chars}:1}"
    done
}

function check_verdict () {
    verdict=$?
    if [ $verdict -ne 101 ]
    then
        echo "ERROR:Bad_verdict:$verdict"
        exit 200
    fi
}

for i in $(seq 1 $n)
do
    echo "RUN:$i"

    random_string
    flag="TEAM001_"${rand_string}"="

    random_string
    flag_id=${rand_string}

    ./keys.checker.py check $HOST
    check_verdict

    flag_id=$(./keys.checker.py put $HOST $flag_id $flag 1)
    check_verdict
    echo "FLAG_ID:${flag_id}"

    ./keys.checker.py get $HOST "${flag_id}" "${flag}" 1
    check_verdict

done
