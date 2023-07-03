#!/usr/bin/env python3
import json
import logging
import random
import string
import requests

import sys
import traceback

OK, CORRUPT, MUMBLE, DOWN, CHECKER_ERROR = 101, 102, 103, 104, 110

PORT = 8080

MAIN_COOKIE = "ctf"
SIGN_COOKIE = "ctf.sig"

CHARSET = string.ascii_lowercase + string.digits


def random_str(length):
    return ''.join(random.choice(CHARSET) for i in range(length))


def verdict(exit_code, public="", private=""):
    if private:
        logging.error(private)
    if public:
        logging.info("Public verdict: %r.", public)
        print(public)
    logging.info("Exit with code: %d.", exit_code)
    sys.exit(exit_code)


def info():
    verdict(OK, "\n".join([
        "vulns: 1",
        "public_flag_description: Flag ID is 'Username', flag is 'Flag'."
    ]))


def check(host):
    url = "http://{}:{}/".format(host, PORT)
    logging.debug("URL: %s", url)

    title = "<h1>CTF Qualification Service</h1>"

    response = requests.get(url)
    response.raise_for_status()

    verdict(OK if title in response.text else MUMBLE)


def put(host, flag_id, flag, vuln):
    url = "http://{}:{}/".format(host, PORT)
    logging.debug("URL: %s", url)

    user = random_str(8)
    password = random_str(12)

    data = {
        "user": user,
        "password": password,
        "flag": flag,
        "register": "Register",
    }

    response = requests.post(url, data)
    response.raise_for_status()

    if "User registered." not in response.text:
        verdict(MUMBLE, "No 'User registered.' text in response")

    json_flag_id = json.dumps({
        "public_flag_id": user,
        "password": password,
    }).replace(" ", "")

    verdict(OK, json_flag_id)


def get(host, flag_id, flag, vuln):
    url = "http://{}:{}/".format(host, PORT)
    logging.debug("URL: %s", url)

    json_flag_id = json.loads(flag_id)

    user = json_flag_id["public_flag_id"]
    password = json_flag_id["password"]

    data = {
        "user": user,
        "password": password,
        "login": "Login",
    }

    logging.info("Logging in ...")
    response = requests.post(url, data, allow_redirects=False)
    response.raise_for_status()

    if "no such user" in response.text:
        verdict(MUMBLE, "Cannot log in: no such user")

    if "wrong password" in response.text:
        verdict(MUMBLE, "Cannot log in: wrong password")

    if response.status_code != 302:
        logging.debug("Response text: %r", response.text)
        verdict(MUMBLE, "Response status code: {}, expected 302.".format(response.status_code))

    cookies = response.cookies
    logging.debug("Response cookies: %s ...", dict(cookies))

    if MAIN_COOKIE not in response.cookies:
        verdict(MUMBLE, "Cookie %q not set".format(MAIN_COOKIE))

    if SIGN_COOKIE not in response.cookies:
        verdict(MUMBLE, "Cookie %q not set".format(SIGN_COOKIE))

    logging.info("Getting user data ...")
    response = requests.get(url, cookies=cookies)
    response.raise_for_status()

    if flag in response.text:
        verdict(OK, "Flag found")
    else:
        logging.debug("Response text: %r", response.text)
        verdict(CORRUPT, "Flag not found")


def main(args):
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")

    cmd_mapping = {
        "info":     (info, 0),
        "check":    (check, 1),
        "put":      (put, 4),
        "get":      (get, 4),
    }

    if not args:
        verdict(CHECKER_ERROR, "No args", "No args")

    cmd, args = args[0], args[1:]
    if cmd not in cmd_mapping:
        verdict(CHECKER_ERROR, "Checker error", "Wrong command %s" % cmd)

    handler, args_count = cmd_mapping[cmd]
    if len(args) != args_count:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for %s (%d, expected: %d)" %
                (cmd, len(args), args_count))

    try:
        handler(*args)
    except ConnectionRefusedError as E:
        verdict(DOWN, "Connect refused", "Connect refused: %s" % E)
    except ConnectionError as E:
        if RECEIVED_SOMETHING:
            verdict(MUMBLE, "Connection aborted", "Connection aborted: %s" % E)
        else:
            verdict(DOWN, "Connection aborted (no data received)", "Connection aborted (no data received): %s" % E)
    except OSError as E:
        verdict(DOWN, "Connect error", "Connect error: %s" % E)
    except Exception as E:
        verdict(CHECKER_ERROR, "Checker error", "Checker error: %s" % traceback.format_exc())
    verdict(CHECKER_ERROR, "Checker error", "No verdict")


if __name__ == "__main__":
    main(args=sys.argv[1:])
