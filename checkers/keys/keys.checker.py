#!/usr/bin/env python3

import json
import logging
import os
import re
import requests
import sys
import traceback

from checker_helper import *

logging.basicConfig(level=logging.DEBUG)

PORT = 3000
TIMEOUT = 30
CHECKER_DIRECT_CONNECT = os.environ.get("CHECKER_DIRECT_CONNECT")
PRIVATE_KEY_RE = re.compile(r'(-----BEGIN PRIVATE KEY-----.*?-----END PRIVATE KEY-----)', re.MULTILINE | re.DOTALL)
PUBLIC_KEY_RE = re.compile(r'(-----BEGIN PUBLIC KEY-----.*?-----END PUBLIC KEY-----)', re.MULTILINE | re.DOTALL)


def info():
    verdict(OK, "vulns: 1\npublic_flag_description: Flag ID is the user's login, flag is the comment")


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
    login = flag_id

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
        verdict(MUMBLE, "No private key", f"Can't find the private key for login:{login}, resp:{resp.text}")
    private_key = m.group(1)

    m = PUBLIC_KEY_RE.search(resp.text)
    if not m:
        verdict(MUMBLE, "No public key", f"Can't find the public key for login:{login}, resp:{resp.text}")
    public_key = m.group(1)

    ret = json.dumps({
        "login": login,
        "public_flag_id": login,
        "public_key": public_key,
        "private_key": private_key,
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

    trace(f"prepare_get : {flag_id}, {flag_data} {vuln}")

    url = f'{_url_prefix}/check.php'
    trace(f"get0({url})")

    form_data = {
        'login': login,
        'private_key': private_key,
    }

    resp = requests.post(url, form_data)
    if resp.status_code in (400, 404):
        verdict(CORRUPT, "Wrong flag", f"Cant find login '{login}' ({resp.status_code})")

    resp.raise_for_status()

    if flag_data not in resp.text:
        verdict(CORRUPT, "Wrong flag", f"'{flag_data}' NOT IN '{resp.text}'")

    url = f'{_url_prefix}/key.php'
    trace(f"get1({url})")

    resp = requests.get(url, {'login' : login})
    resp.raise_for_status()

    m = PUBLIC_KEY_RE.search(resp.text)
    if not m:
        verdict(MUMBLE, "No public key", f"Can't find the public key login:{login}, resp:{resp.text}")
    public_key_from_service = m.group(1).strip()

    if public_key != public_key_from_service:
        verdict(MUMBLE, "Cant find public key", f"Can't find the public key login:{login}, resp:{resp.text}")

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
