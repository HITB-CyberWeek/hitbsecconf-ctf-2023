#!/usr/bin/env python3
import json
import logging
import os
import random
import string

import requests

import sys
import traceback

OK, CORRUPT, MUMBLE, DOWN, CHECKER_ERROR = 101, 102, 103, 104, 110

SKIP_PROXY = os.getenv("SKIP_PROXY") == "1"

PORT = 80 if SKIP_PROXY else 443
PROTOCOL = "http" if SKIP_PROXY else "https"

MAIN_COOKIE = "ctf"

CHARSET = string.ascii_lowercase + string.digits


def random_str(length):
    return ''.join(random.choice(CHARSET) for i in range(length))


def ellipsis_str(s):
    limit = 1600
    return (s[:limit] + '..') if len(s) > limit else s


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
        "public_flag_description: Flag ID is the username, flag is the password for some website"
    ]))


def check(host):
    url = "{}://{}:{}/".format(PROTOCOL, host, PORT)
    response = requests.get(url)
    response.raise_for_status()

    expected = "<h1>CTF Password Manager Service</h1>"
    if expected in response.text:
        verdict(OK)
    verdict(MUMBLE, "Service's greeting ({!r}) not found".format(expected))


def register(host, user, password):
    logging.info("Registering %r with password %r ...", user, password)
    data = {
        "user": user,
        "password": password,
        "register": "Register",
    }

    url = "{}://{}:{}/".format(PROTOCOL, host, PORT)
    response = requests.post(url, data)
    response.raise_for_status()

    expected = "You have successfully registered! Now you may log in."
    if expected not in response.text:
        verdict(MUMBLE, "No {!r} text in response".format(expected))

    logging.info("Registration OK: found %r text.", expected)


def login(host, user, password):
    logging.info("Logging in as user %r with password %r ...", user, password)
    data = {
        "user": user,
        "password": password,
        "login": "Login",
    }

    url = "{}://{}:{}/".format(PROTOCOL, host, PORT)
    response = requests.post(url, data, allow_redirects=False)
    response.raise_for_status()

    if "Invalid credentials" in response.text:
        verdict(MUMBLE, "Cannot log in: Invalid credentials")

    if response.status_code != 302:
        logging.debug("Response text: %r", ellipsis_str(response.text))
        verdict(MUMBLE, "Response status code: {}, expected 302.".format(response.status_code))

    cookies = response.cookies
    logging.debug("Response cookies: %s ...", dict(cookies))

    if MAIN_COOKIE not in response.cookies:
        verdict(MUMBLE, "Cookie {!r} not set".format(MAIN_COOKIE))
    logging.info("Found %r cookie.", MAIN_COOKIE)

    response = requests.get(url, cookies=cookies)
    response.raise_for_status()

    expected = "Welcome, <b>{}</b>!".format(user)
    if expected not in response.text:
        logging.debug("Response text: %r", ellipsis_str(response.text))
        verdict(MUMBLE, "No {!r} text in response".format(expected))
    logging.info("Found %r text.", expected)

    return cookies, response.text


def add_password(host, cookies, address, user, password):
    logging.info("Adding password %r for address %r of user %r ...", password, address, user)

    data = {
        "address": address,
        "user": user,
        "password": password,
    }

    url = "{}://{}:{}/add".format(PROTOCOL, host, PORT)
    response = requests.post(url, cookies=cookies, data=data)
    response.raise_for_status()

    if address not in response.text:
        verdict(MUMBLE, "No address {!r} text in response".format(address))

    if user not in response.text:
        verdict(MUMBLE, "No user {!r} text in response".format(user))

    if password not in response.text:
        verdict(MUMBLE, "No password {!r} text in response".format(password))


def logout(host, cookies):
    logging.info("Logging out ...")

    url = "{}://{}:{}/logout".format(PROTOCOL, host, PORT)
    response = requests.post(url, cookies=cookies)
    response.raise_for_status()


def put(host, flag_id, flag, vuln):
    user = random_str(8)
    password = random_str(12)

    register(host, user, password)
    cookies, _ = login(host, user, password)

    address = "https://www.{}.{}.com".format(random_str(4), random_str(8))
    add_password(host, cookies, address, user, flag)

    logout(host, cookies)

    json_flag_id = json.dumps({
        "public_flag_id": user,
        "password": password,
    }).replace(" ", "")

    verdict(OK, json_flag_id)


def get(host, flag_id, flag, vuln):
    url = "{}://{}:{}/".format(PROTOCOL, host, PORT)

    json_flag_id = json.loads(flag_id)

    user = json_flag_id["public_flag_id"]
    password = json_flag_id["password"]

    cookies, text = login(host, user, password)
    logout(host, cookies)

    if flag in text:
        verdict(OK, "Flag found")

    logging.debug("Response text: %r", ellipsis_str(text))
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
        verdict(DOWN, "Connection refused", "Connection refused: %s" % E)
    except ConnectionError as E:
        verdict(MUMBLE, "Connection aborted", "Connection aborted: %s" % E)
    except OSError as E:
        verdict(DOWN, "Connection error", "Connection error: %s" % E)
    except Exception:
        verdict(CHECKER_ERROR, "Checker error", "Checker error: %s" % traceback.format_exc())
    verdict(CHECKER_ERROR, "Checker error", "No verdict")


if __name__ == "__main__":
    main(args=sys.argv[1:])
