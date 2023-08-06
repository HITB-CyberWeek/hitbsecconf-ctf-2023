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
PRIVATE_KEY_RE = re.compile(r'(-----BEGIN PRIVATE KEY-----.*?-----END PRIVATE KEY-----)', re.MULTILINE | re.DOTALL)
PUBLIC_KEY_RE = re.compile(r'(-----BEGIN PUBLIC KEY-----.*?-----END PUBLIC KEY-----)', re.MULTILINE | re.DOTALL)


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
    if len(args) != 4:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for put()")
    host, flag_id, flag, vuln = args
    login = get_random_string(10, 20)

    url = url_prefix(host)
    url = f'{url}/generate.php'

    trace(f"put0({url}, {flag_id}, {flag}, {vuln}, {login})")

    form_data = {
        'login': login,
        'comment': flag,
    }

    resp = requests.post(url, form_data)
    resp.raise_for_status()

    m = PRIVATE_KEY_RE.search(resp.text)
    if not m:
        verdict(MUMBLE, "No private key", f"Cant find private key in resp:{resp.text}")
    private_key = m.group(1)

    m = PUBLIC_KEY_RE.search(resp.text)
    if not m:
        verdict(MUMBLE, "No public key", f"Cant find public key in resp:{resp.text}")
    public_key = m.group(1)

    ret = json.dumps({
        "login": login,
        "public_flag_id": f"login: {login}",
        "public_key": public_key,
        "private_key": private_key,
        "orig_flag_id": flag_id,
    })

    verdict(OK, ret)


@checker_action
def get(args):
    if len(args) != 4:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for get()")
    host, flag_id, flag_data, vuln = args
    data = json.loads(flag_id)
    login = data['login']
    public_key = data['public_key']
    private_key = data['private_key']

    _url_prefix = url_prefix(host)

    url = f'{_url_prefix}/key.php'
    trace("get0(%s, %s, %s, %s)" % (url, flag_id, flag_data, vuln))

    resp = requests.get(url, {'login' : login})
    resp.raise_for_status()

    m = PUBLIC_KEY_RE.search(resp.text)
    if not m:
        verdict(MUMBLE, "No public key", f"Cant find public key in resp:{resp.text}")
    public_key_from_service = m.group(1).strip()

    if public_key != public_key_from_service:
        verdict(CORRUPT, "Cant find public key", f"Cant find public key in resp:{resp.text}")

    url = f'{_url_prefix}/check.php'
    trace("get1(%s, %s, %s, %s)" % (url, flag_id, flag_data, vuln))

    form_data = {
        'login': login,
        'private_key': private_key,
    }

    resp = requests.post(url, form_data)
    resp.raise_for_status()

    if flag_data not in resp.text:
        verdict(CORRUPT, "Wrong flag", f"'{flag_data}' NOT IN '{resp.text}'")
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
