#!/usr/bin/env python3

import json
import logging
import os
import random
import requests
import string
import sys
import time
import traceback

logging.basicConfig(format="%(asctime)s [%(process)d] %(levelname)-8s %(message)s",
                    level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stderr)])

OK, CORRUPT, MUMBLE, DOWN, CHECKER_ERROR = 101, 102, 103, 104, 110
TIMEOUT = 5


def verdict(exit_code, public="", private=""):
    if public:
        print(public)
    if private:
        print(private, file=sys.stderr)
    sys.exit(exit_code)


def random_name(length=10):
    return ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=length))


def get_base_url(host):
    base_url = f"http://{host}/"

    try:
        r = requests.options(base_url, timeout=3, allow_redirects=False)
        if r.status_code > 300 and r.status_code < 400 and r.headers["Location"]:
            base_url = r.headers["Location"]
            if not base_url[-1] == '/':
                base_url += '/'
    except:
        pass

    return base_url


def info():
    verdict(OK, "vulns: 1\npublic_flag_description: Flag ID is a document title and user's org in format title@org, flag is a content of the document with title from flag ID")


def check(host):
    login = random_name()
    password = random_name()
    org = random_name(length=5)
    logging.info(f"Try to register user '{login}' with password '{password}' at org '{org}'")

    base_url = get_base_url(host)
    url = f"{base_url}register"
    logging.info(f"Check register url '{url}' on host '{host}'")

    r = requests.post(url, timeout=TIMEOUT, json={"login": login, "password": password, "org": org})
    if r.status_code != 200:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /register")
    try:
        jr = r.json()
        logging.debug(f"Login in answer: '{jr['login']}'")
        if jr["login"] != login:
            verdict(MUMBLE, public="Wrong login in answer on /register")
    except Exception as e:
        logging.debug(traceback.format_exc())
        verdict(MUMBLE, public="Invalid answer")
    invalid_login = random.choice(string.punctuation) + login + random.choice(string.punctuation)
    invalid_org = random.choice(string.punctuation) + org + random.choice(string.punctuation)
    r = requests.post(url, timeout=TIMEOUT, json={"login": invalid_login, "password": password,"org": invalid_org})
    if r.status_code != 400:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /register")

    url = f"{base_url}login"
    logging.info(f"Check login url '{url}' on host '{host}'")
    r = requests.post(url, timeout=TIMEOUT, json={"login": login, "password": password, "org": org})
    if r.status_code != 204:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /login")
    if not "docs_session" in r.cookies:
        verdict(MUMBLE, public=f"Wrong cookie 'docs_session' on /login")

    verdict(OK)


def put(host, flag_id, flag, vuln):
    login = random_name()
    password = random_name()
    org = random_name(length=5)
    logging.info(f"Try to register user '{login}' with password '{password}' at org '{org}'")

    user_info = {"login": login, "password": password, "org": org}
    state = {"public_flag_id": f"{flag_id}@{org}", "flag_id": flag_id, "user_info": user_info}

    base_url = get_base_url(host)
    session = requests.Session()

    url = f"{base_url}register"
    r = session.post(url, timeout=TIMEOUT, json=user_info)
    if r.status_code != 200:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /register")

    url = f"{base_url}login"
    r = session.post(url, timeout=TIMEOUT, json=user_info)
    if r.status_code != 204:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /login")

    url = f"{base_url}docs"
    r = session.post(url, timeout=TIMEOUT, json={"title": flag_id, "shares": []})
    if r.status_code != 201:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /docs")
    try:
        doc_id = r.json()["id"]
        url = f"{base_url}contents"
        r = session.post(url, timeout=TIMEOUT, json={"doc_id": doc_id, "data": flag})
        if r.status_code != 201:
            verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /contents")
    except Exception as e:
        logging.debug(traceback.format_exc())
        verdict(MUMBLE, public="Invalid answer on /docs")

    verdict(OK, json.dumps(state))


def get(host, flag_id, flag, vuln):
    state = json.loads(flag_id)

    base_url = get_base_url(host)
    session = requests.Session()

    url = f"{base_url}login"
    r = session.post(url, timeout=TIMEOUT, json=state["user_info"])
    if r.status_code != 204:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /login")

    url = f"{base_url}docs"
    r = session.get(url, timeout=TIMEOUT)
    if r.status_code != 200:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /docs")
    try:
        doc_id = None
        for doc in r.json()["docs"]:
            if doc["title"] == state["flag_id"]:
                doc_id = doc["id"]
                break

        if not doc_id:
            verdict(MUMBLE, public=f"Invalid answer on /docs; document with title {state['flag_id']} not found")

        url = f"{base_url}contents/{doc_id}"
        r = session.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /contents")

        if r.text != flag:
            verdict(CORRUPT, public=f"Wrong data in document with title {state['flag_id']}")
    except Exception as e:
        logging.debug(traceback.format_exc())
        verdict(MUMBLE, public="Invalid answer on /docs")

    verdict(OK)

def main(args):
    CMD_MAPPING = {
        "info": (info, 0),
        "check": (check, 1),
        "put": (put, 4),
        "get": (get, 4),
    }

    if not args:
        verdict(CHECKER_ERROR, "No args", "No args")

    cmd, args = args[0], args[1:]
    if cmd not in CMD_MAPPING:
        verdict(CHECKER_ERROR, "Checker error", f"Wrong command {cmd}")

    handler, args_count = CMD_MAPPING[cmd]
    if len(args) != args_count:
        verdict(CHECKER_ERROR, "Checker error",
                f"Wrong args count for {cmd}")

    try:
        handler(*args)
    except (requests.Timeout, requests.ConnectionError):
        logging.debug(traceback.format_exc())
        verdict(DOWN, public="Can't get HTTP response")

    verdict(CHECKER_ERROR, "Checker error", "No verdict")


if __name__ == "__main__":
    main(args=sys.argv[1:])
