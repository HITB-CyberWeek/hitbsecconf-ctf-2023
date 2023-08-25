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
import urllib3

from requests.adapters import HTTPAdapter, Retry

logging.basicConfig(format="%(asctime)s [%(process)d] %(levelname)-8s %(message)s",
                    level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stderr)])

OK, CORRUPT, MUMBLE, DOWN, CHECKER_ERROR = 101, 102, 103, 104, 110

TIMEOUT = urllib3.util.Timeout(connect=1.0, read=3.0)
RETRIES = Retry(total=3, backoff_factor=0.3, status_forcelist=[ 500, 502, 503, 504 ])


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
        r = requests.options(base_url, timeout=TIMEOUT, allow_redirects=False)
        if r.status_code > 300 and r.status_code < 400 and r.headers["Location"]:
            base_url = r.headers["Location"]
            if not base_url[-1] == '/':
                base_url += '/'
    except:
        pass

    return base_url


def info():
    verdict(OK, "vulns: 1\npublic_flag_description: Flag ID is the document's title and user's org in \"title@org\" format, flag is the content of the document with this title")


def check(host):
    verdict(OK)


def put(host, flag_id, flag, vuln):
    user1 = {"login": random_name(), "password": random_name(), "org": random_name(length=5)}
    logging.info(f"user1 {user1}")
    user2 = {"login": random_name(), "password": random_name(), "org": random_name(length=5)}
    logging.info(f"user2 {user2}")

    state = {"public_flag_id": f"{flag_id}@{user1['org']}", "flag_id": flag_id, "user1": user1, "user2": user2}

    base_url = get_base_url(host)
    session1 = requests.Session()
    session2 = requests.Session()
    session1.mount('http://', HTTPAdapter(max_retries=RETRIES))
    session1.mount('https://', HTTPAdapter(max_retries=RETRIES))
    session2.mount('http://', HTTPAdapter(max_retries=RETRIES))
    session2.mount('https://', HTTPAdapter(max_retries=RETRIES))

    url = f"{base_url}register"
    r = session1.post(url, timeout=TIMEOUT, json=user1)
    if r.status_code != 200:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /register")
    try:
        user1_id = r.json()["user_id"]
        logging.info(f"Registered user1 with id: {user1_id}")
        state["user1"]["id"] = user1_id
    except Exception as e:
        logging.debug(traceback.format_exc())
        verdict(MUMBLE, public="Invalid answer on /register")

    r = session2.post(url, timeout=TIMEOUT, json=user2)
    if r.status_code != 200:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /register")
    try:
        user2_id = r.json()["user_id"]
        logging.info(f"Registered user2 with id: {user2_id}")
        state["user2"]["id"] = user2_id
    except Exception as e:
        logging.debug(traceback.format_exc())
        verdict(MUMBLE, public="Invalid answer on /register")

    url = f"{base_url}login"
    r = session1.post(url, timeout=TIMEOUT, json=user1)
    if r.status_code != 204:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /login")
    r = session2.post(url, timeout=TIMEOUT, json=user2)
    if r.status_code != 204:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /login")

    url = f"{base_url}docs"
    r = session1.post(url, timeout=TIMEOUT, json={"title": flag_id, "shares": []})
    if r.status_code != 201:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /docs")
    try:
        doc_id = r.json()["id"]
        url = f"{base_url}contents"
        r = session1.post(url, timeout=TIMEOUT, json={"doc_id": doc_id, "data": flag})
        if r.status_code != 201:
            verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /contents")
    except Exception as e:
        logging.debug(traceback.format_exc())
        verdict(MUMBLE, public="Invalid answer on /docs")

    url = f"{base_url}docs"
    r = session1.post(url, timeout=TIMEOUT, json={"title": random_name(), "shares": [user2_id]})
    if r.status_code != 201:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /docs")

    url = f"{base_url}docs"
    r = session2.get(url, timeout=TIMEOUT)
    if r.status_code != 200:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /docs")
    try:
        docs = r.json()["docs"]
        if len(docs) != 1:
            verdict(MUMBLE, public=f"Invalid answer on /docs")
        if docs[0] == state["flag_id"]:
            verdict(MUMBLE, public=f"Invalid answer on /docs")
    except Exception as e:
        logging.debug(traceback.format_exc())
        verdict(MUMBLE, public="Invalid answer on /docs")

    verdict(OK, json.dumps(state))


def get(host, flag_id, flag, vuln):
    state = json.loads(flag_id)

    base_url = get_base_url(host)
    session1 = requests.Session()
    session2 = requests.Session()
    session1.mount('http://', HTTPAdapter(max_retries=RETRIES))
    session1.mount('https://', HTTPAdapter(max_retries=RETRIES))
    session2.mount('http://', HTTPAdapter(max_retries=RETRIES))
    session2.mount('https://', HTTPAdapter(max_retries=RETRIES))

    url = f"{base_url}login"
    r = session1.post(url, timeout=TIMEOUT, json=state["user1"])
    if r.status_code != 204:
        verdict(CORRUPT, public=f"Wrong HTTP status code ({r.status_code}) on /login")
    r = session2.post(url, timeout=TIMEOUT, json=state["user2"])
    if r.status_code != 204:
        verdict(CORRUPT, public=f"Wrong HTTP status code ({r.status_code}) on /login")

    url = f"{base_url}users/{state['user2']['id']}"
    logging.info(f"Update org of user2")
    r = session2.put(url, timeout=TIMEOUT, json={"org": state["user1"]["org"]})
    if r.status_code != 204:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on PUT /users")

    url = f"{base_url}docs"
    r = session2.get(url, timeout=TIMEOUT)
    if r.status_code != 200:
        verdict(MUMBLE, public=f"Wrong HTTP status code ({r.status_code}) on /docs")
    try:
        docs = r.json()["docs"]
        if len(docs) != 2:
            verdict(MUMBLE, public=f"Invalid answer on /docs")
        doc_id = None
        for doc in docs:
            if doc["title"] == state["flag_id"]:
                doc_id = doc["id"]
                break

        if not doc_id:
            verdict(MUMBLE, public=f"Invalid answer on /docs; document with title {state['flag_id']} not found")

        url = f"{base_url}contents/{doc_id}"
        r = session1.get(url, timeout=TIMEOUT)
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
    except (requests.Timeout, requests.ConnectionError, requests.exceptions.RetryError):
        logging.debug(traceback.format_exc())
        verdict(DOWN, public="Can't get HTTP response")

    verdict(CHECKER_ERROR, "Checker error", "No verdict")


if __name__ == "__main__":
    main(args=sys.argv[1:])
