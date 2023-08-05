#!/usr/bin/env python3

import json
import os
import random
import re
import requests
import string
import sys
import traceback

requests.packages.urllib3.disable_warnings()
from checker_helper import *

PORT = 3000
TIMEOUT = 30
CHECKER_DIRECT_CONNECT = os.environ.get("CHECKER_DIRECT_CONNECT")
# KEYS_COUNT_RE = re.compile(r'Currently stored keys: (\d+)')


def info():
    verdict(OK, "vulns: 1\npublic_flag_description: TODO")


def get_random_string(min_len, max_len):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(random.randint(min_len, max_len)))


def url_prefix(host):
    if CHECKER_DIRECT_CONNECT == "1":
        return f"http://{host}:{PORT}"
    return f"https://{host}"

@checker_action
def check(args):
    if len(args) != 1:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for check()")
    host = args[0]
    url = url_prefix(host)
    trace(f"check({url})")

    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()

    # content = resp.text
    # match = KEYS_COUNT_RE.search(content)
    # if not match:
    #     verdict(MUMBLE, "Bad index page; can't find keys count", f"CONTENT:{content}")

    verdict(OK)


@checker_action
def put(args):
    verdict(OK, flag_id)


@checker_action
def get(args):
    verdict(OK)

def main(args):
    if len(args) == 0:
        verdict(CHECKER_ERROR, "Checker error", "No args")
    try:
        if args[0] == "info":
            info()
        elif args[0] == "check":
            check(args[1:])
        elif args[0] == "put":
            put(args[1:])
        elif args[0] == "get":
            get(args[1:])
        else:
            verdict(CHECKER_ERROR, "Checker error", "Wrong action: " + args[0])
    except Exception as e:
        verdict(CHECKER_ERROR, "Checker error", "Exception: %s" % traceback.format_exc())

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
        verdict(CHECKER_ERROR, "Checker error", "No verdict")
    except Exception as e:
        verdict(CHECKER_ERROR, "Checker error", "Exception: %s" % e)
