#!/usr/bin/env python3
import json
import logging
import os
import random
import string
import time
import re
from typing import Optional, Tuple
import copy

import requests

import sys
import traceback

OK, CORRUPT, MUMBLE, DOWN, CHECKER_ERROR = 101, 102, 103, 104, 110

SKIP_PROXY = os.getenv("SKIP_PROXY") == "1"

PORT = 80 if SKIP_PROXY else 443
PROTOCOL = "http" if SKIP_PROXY else "https"

HACK_PROBABILITY = 5
HACK_SLEEP = 3
SUBMIT_FLAG_PROBABILITY = 3

MAIN_COOKIE = "ctf"
SIGN_COOKIE = "ctf.sig"

CHARSET = string.ascii_lowercase + string.digits


def random_str(length):
    return ''.join(random.choice(CHARSET) for i in range(length))


PLATFORM_API_ENDPOINT = os.getenv("PLATFORM_API_ENDPOINT") or "https://ctf.hackerdom.ru/api/"
PLATFORM_EVENT_SLUG = os.getenv("PLATFORM_EVENT_SLUG") or "hitb-ctf-phuket-2023"
PLATFORM_USERNAME = os.getenv("PLATFORM_USERNAME") or "admin"
PLATFORM_PASSWORD = os.getenv("PLATFORM_PASSWORD") or "admin"

PLATFORM_TIMEOUT = 5 # seconds

CHECKSYSTEM_FLAGS_ENDPOINT = os.getenv("CHECKSYSTEM_FLAGS_ENDPOINT") or "https://training.ctf.hitb.org/flags"
CHECKSYSTEM_TOKEN = os.getenv("CHECKSYSTEM_TOKEN") or "<unknown-token>"

CHECKSYSTEM_TIMEOUT = 5 # seconds


def add_training_tag(team_host: str, tag: str):
    """
    Special method for HITB CTF Training: it makes a request to https://ctf.hackerdom.ru and 
    adds "tag" (as an attribute) to the team.
    """
    for retry in range(3):
        try:
            _add_training_tag(team_host, tag)
            break
        except Exception as e:
            logging.warning(f"[{retry + 1}/3] Can not add tag to the team: {e}", exc_info=e)


def _add_training_tag(team_host: str, tag: str):
    registration_id, attributes = _find_registration_by_team_host(team_host)
    if registration_id is None:
        logging.error(f"Did not found a registration for team with host {team_host!r}")
        return

    logging.info(f"Found registration for team with host {team_host!r}: #{registration_id}")

    current_attributes = copy.deepcopy(attributes)
    if "training" not in attributes:
        attributes["training"] = []
    if tag in attributes["training"]:
        logging.info(f"Team already has the tag {tag!r}, don't add it again")
        return
    attributes["training"].append(tag)

    url = f"{PLATFORM_API_ENDPOINT}registrations/{PLATFORM_EVENT_SLUG}/{registration_id}/attributes/"
    data = {"current_attributes": current_attributes, "new_attributes": attributes}
    logging.info(f"Sending request to {url} with following content: {data!r}")
    r = requests.post(url, json=data, auth=(PLATFORM_USERNAME, PLATFORM_PASSWORD), timeout=PLATFORM_TIMEOUT)
    r.raise_for_status()



def _find_registration_by_team_host(team_host: str) -> Tuple[Optional[int], dict]:
    m = re.search(r"team(\d+)", team_host)
    if not m:
        return None, {}
    team_id = int(m.group(1))

    url = f"{PLATFORM_API_ENDPOINT}registrations/{PLATFORM_EVENT_SLUG}/"
    logging.info(f"Requesting registrations list from {url}")
    r = requests.get(url, timeout=PLATFORM_TIMEOUT)
    r.raise_for_status()
    try:
        result = r.json()
    except requests.exceptions.JSONDecodeError:
        logging.info(f"Response from the server: {r.text}")
        raise
    if ("status" not in result or result["status"] != "ok" or 
        "registrations" not in result or not isinstance(result["registrations"], list)):
        raise ValueError(f"Invalid response from {url}: result")

    if team_id - 1 >= len(result["registrations"]):
        return None, {}
    
    registration = result["registrations"][team_id - 1]
    return int(registration["id"]), registration["attributes"]


def send_flag_to_checksystem(flag: str):
    if not CHECKSYSTEM_TOKEN:
        return
    try:
        logging.info(f"Trying to submit flag {flag} to the checksystem {CHECKSYSTEM_FLAGS_ENDPOINT}")
        requests.put(CHECKSYSTEM_FLAGS_ENDPOINT, headers={"X-Team-Token": CHECKSYSTEM_TOKEN}, json=[flag], timeout=CHECKSYSTEM_TIMEOUT)
    except Exception as e:
        logging.warning(f"Can not submit flag to the checksystem: {e}", exc_info=e)


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
    url = "{}://{}:{}/".format(PROTOCOL, host, PORT)
    logging.debug("URL: %s", url)

    title = "<h1>CTF Training Service</h1>"

    response = requests.get(url)
    response.raise_for_status()

    outcome = OK if title in response.text else MUMBLE
    if outcome == OK:
        add_training_tag(host, "started-service")
    verdict(outcome)


def put(host, flag_id, flag, vuln):
    url = "{}://{}:{}/".format(PROTOCOL, host, PORT)
    logging.debug("URL: %s", url)

    user = random_str(8)
    password = random_str(12)

    logging.info("Registering %r with password %r ...", user, password)

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
    url = "{}://{}:{}/".format(PROTOCOL, host, PORT)
    logging.debug("URL: %s", url)

    json_flag_id = json.loads(flag_id)

    user = json_flag_id["public_flag_id"]
    password = json_flag_id["password"]

    data = {
        "user": user,
        "password": password,
        "login": "Login",
    }

    logging.info("Logging in as %r ...", user)
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
        verdict(MUMBLE, "Cookie %r not set".format(MAIN_COOKIE))

    if SIGN_COOKIE not in response.cookies:
        verdict(MUMBLE, "Cookie %r not set".format(SIGN_COOKIE))

    logging.info("Getting user data ...")
    response = requests.get(url, cookies=cookies)
    response.raise_for_status()

    if flag in response.text:
        verdict(OK, "Flag found")

        # After successful "get" we can try to hack this team: probably flag is available even without authentication?
        if random.randint(0, HACK_PROBABILITY) == 0:
            time.sleep(random.random() * HACK_SLEEP)
            hack(host, user, flag)
    else:
        logging.debug("Response text: %r", response.text)
        verdict(CORRUPT, "Flag not found")


def hack(host, user, flag):
    url = "{}://{}:{}/".format(PROTOCOL, host, PORT)
    logging.debug("URL: %s", url)

    logging.info("Hacking user %r ...", user)

    data = {
        "user": user,
    }
    response = requests.post(url, data)
    if response.status_code != 200:
        logging.info("Hack response code %r. Service is NOT vulnerable.", response.status_code)
        return

    for line in response.text.split("\n"):
        if flag in line:
            logging.info("Found flag: %r! Service is vulnerable.", line.strip())
            if random.randint(0, SUBMIT_FLAG_PROBABILITY) == 0:
                send_flag_to_checksystem(flag)
            return        
            
    add_training_tag(host, "defended")
    logging.info("Flag not found. Service is NOT vulnerable.")


def main(args):
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")

    cmd_mapping = {
        "info":     (info, 0),
        "check":    (check, 1),
        "put":      (put, 4),
        "get":      (get, 4),
        "hack":     (hack, 3),
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
