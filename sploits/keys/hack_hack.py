#!/usr/bin/env python3

import argparse
import json
import os
import random
import re
import requests
import string
import subprocess
import sys

requests.packages.urllib3.disable_warnings()

CHECKER_PATH = "../../checkers/keys/keys.checker.py"
SPLOIT_PATH = "./hack.php"
TIMEOUT = 30


def get_random_string(min_len, max_len, alphabet=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(alphabet) for i in range(random.randint(min_len, max_len)))


def set_flag(checker_path, host):
    flag_id = get_random_string(10, 10)
    flag = "TEAM001_" + get_random_string(32, 32, alphabet=string.ascii_uppercase + string.digits)

    proc = subprocess.run([checker_path, 'put', host, flag_id, flag, "1"], stdout=subprocess.PIPE, env=os.environ, timeout=TIMEOUT, text=True, encoding='utf-8')
    ret = proc.stdout
    assert proc.returncode == 101  # OK

    ret_data = json.loads(ret)
    public_flag_id = ret_data['public_flag_id']

    return public_flag_id, flag


def hack(sploit_path, host, flag_id):
    proc = subprocess.run([sploit_path, host, flag_id], stdout=subprocess.PIPE, env=os.environ, check=True, timeout=TIMEOUT, text=True, encoding='utf-8')
    ret = proc.stdout
    flag = ret.strip()

    return flag


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("host", help="host")
    parser.add_argument("--checker_path", default=os.environ.get('CHECKER_PATH', CHECKER_PATH))
    parser.add_argument("--sploit_path", default=os.environ.get('SPLOIT_PATH', SPLOIT_PATH))
    args = parser.parse_args()

    flag_id, flag_generated = set_flag(args.checker_path, args.host)
    flag_from_service = hack(args.sploit_path, args.host, flag_id)

    if flag_generated != flag_from_service:
        print(f"Ooopps! flag_generated={flag_generated} flag_from_service={flag_from_service} NOT MATCHED!")
        sys.exit(1)

    print(f"HACKED! flags={flag_from_service}")


if __name__ == "__main__":
    main()
