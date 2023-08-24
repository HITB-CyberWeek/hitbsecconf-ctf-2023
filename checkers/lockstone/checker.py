#!/usr/bin/env python3

import sys
import socket
import hashlib
import random
import time
import json
import traceback
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import requests

OK, CORRUPT, MUMBLE, DOWN, CHECKER_ERROR = 101, 102, 103, 104, 110

PORT = 443
TIMEOUT = 15

ABC = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"

def gen_rand_string(l=12):
    return "".join(random.choice(ABC) for i in range(l))



def verdict(exit_code, public="", private=""):
    if public:
        print(public)
    if private:
        print(private, file=sys.stderr)
    sys.exit(exit_code)


def info():
    verdict(OK, "vulns: 1\npublic_flag_description: Flag ID is the user's login, flag is somewhere near\n")



def call_api(s, ip, data):
    return s.post(f"https://{ip}:{PORT}/api/graphql", json=data, verify=False).json().get("data", {})


def gen_login():
    ABC = "abcdefghijklmnopqrstuvwxyz01234567890!@#$%^&*(){}'<>ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    name = "".join(random.choice(ABC) for i in range(random.randrange(6, 10)))

    if random.random() < 0.01:
        return name + ";select id,flag from users"
    if random.random() < 0.01:
        return name + "' union select id,flag from users -- "
    if random.random() < 0.01:
        return name + f"; union select get_flag(id, {random.randrange(1, 100)}) -- "
    if random.random() < 0.01:
        return name + f";select getFlag(id, {random.randrange(1, 100)}) "
    return name


def gen_password():
    return "".join(random.choice(ABC) for i in range(16))


def gen_flag():
    return "".join(random.choice(ABC) for i in range(8))


def create_user(s, host, login, password, flag):
    data = {
        "variables": {
            "data": {
                "login": login,
                "flag": flag,
                "password": password
            }
        },
        "query": CREATE_USER_MUTATION
    }

    resp = call_api(s, host, data=data)
    return resp.get("item", {}).get("label", "")


LIST_USER_QUERY = """query ($where: UserWhereInput, $take: Int!, $skip: Int!, $orderBy: [UserOrderByInput!]) {
    items: users(where: $where, take: $take, skip: $skip, orderBy: $orderBy) {
        id
        login
        flag
        __typename
    }
    count: usersCount(where: $where)
}"""


def check(host):
    login = gen_login()
    password = gen_password()
    flag = gen_flag()

    s = requests.session()
    created_login = create_user(s, host, login, password, flag)

    if not created_login:
        verdict(MUMBLE, "Failed to register a new user", "Failed to register: %s %s" % (login, password))

    data = {
        "variables": {
            "where": {
                "OR": []
            },
            "take": 50,
            "skip": 0,
            "orderBy": [{
                "createdAt": "desc"
            }]
        },
        "query": LIST_USER_QUERY
    }

    resp = call_api(s, host, data=data)

    items = resp.get("items", [])
    logins = [item.get("login", "") for item in items]

    if created_login not in logins:
        verdict(MUMBLE, "User list is broken", "User list is broken: %s %s" % (login, password))


    verdict(OK)


CREATE_USER_MUTATION = """mutation ($data: UserCreateInput!) {
    item: createUser(data: $data) {
        id
        label: login
        __typename
    }
}"""


def put(host, flag_id, flag, vuln):
    login = gen_login()
    password = gen_password()

    s = requests.session()
    created_login = create_user(s, host, login, password, flag)

    if created_login != login:
        verdict(MUMBLE, "Failed to register a new user", "Failed to register: %s %s" % (login, password))

    verdict(OK, json.dumps({"public_flag_id": login, "login": login, "password": password}))


AUTHENTICATE_MUTATION = """mutation ($identity: String!, $secret: String!) {
    authenticate: authenticateUserWithPassword(login: $identity, password: $secret) {
        ... on UserAuthenticationWithPasswordSuccess {
            item {
                id
                __typename
            }
            __typename
        }
        ... on UserAuthenticationWithPasswordFailure {
            message
            __typename
        }
        __typename
    }
}"""


ITEM_QUERY = """query ItemPage($id: ID!) {
    item: user(where: {id: $id}) {
        id
        login
        flag
        password {
            isSet
            __typename
        }
        createdAt
        __typename
    }
}

"""


def get(host, flag_id, flag, vuln):
    s = requests.session()
    try:
        info = json.loads(flag_id)
        login = info["login"]
        password = info["password"]
    except Exception:
        verdict(CHECKER_ERROR, "Bad flag id", "Bad flag_id: %s" % traceback.format_exc())

    data = {
        "variables": {
            "identity": login,
            "secret": password
        }, "query": AUTHENTICATE_MUTATION
    }

    resp = call_api(s, host, data=data)

    user_id = resp.get("authenticate", {}).get("item", {}).get("id", "")

    if not user_id:
        verdict(CORRUPT, "Failed to login user", "Failed to login: %s %s" % (login, password))


    data = {
        "operationName": "ItemPage",
        "variables": {"id": user_id},
        "query": ITEM_QUERY
    }

    resp = call_api(s, host, data=data)

    stored_flag = resp.get("item", {}).get("flag", "")

    if stored_flag != flag:
        verdict(CORRUPT, "No such flags",
            "No such flag %s, stored_flag %d" % (flag, stored_flag))


    verdict(OK, flag_id)


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
        verdict(CHECKER_ERROR, "Checker error", "Wrong command %s" % cmd)

    handler, args_count = CMD_MAPPING[cmd]
    if len(args) != args_count:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for %s" % cmd)

    try:
        handler(*args)

    except ConnectionRefusedError as E:
        verdict(DOWN, "Connect refused", "Connect refused: %s" % E)
    except ConnectionError as E:
        verdict(MUMBLE, "Connection aborted", "Connection aborted: %s" % E)
    except AttributeError as E:
        verdict(MUMBLE, "Bad data format", "Bad data format: %s" % E)
    except OSError as E:
        verdict(DOWN, "Connect error", "Connect error: %s" % E)
    except Exception as E:
        verdict(CHECKER_ERROR, "Checker error", "Checker error: %s" % traceback.format_exc())
    verdict(CHECKER_ERROR, "Checker error", "No verdict")


if __name__ == "__main__":
    main(args=sys.argv[1:])
