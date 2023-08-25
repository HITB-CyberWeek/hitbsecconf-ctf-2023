#!/usr/bin/env python3.11
import hashlib
import json
import random
import sys
import traceback

import jsonschema.exceptions
import requests
from gornilo import CheckRequest, Verdict, PutRequest, GetRequest, VulnChecker, NewChecker
from requests import HTTPError

import api
import generators

checker = NewChecker()
PORT = 8080


DOWN_EXCEPTIONS = {
    requests.exceptions.ConnectTimeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.ReadTimeout
}
MUMBLE_EXCEPTIONS = {
    requests.exceptions.HTTPError,
    requests.exceptions.JSONDecodeError,
    jsonschema.exceptions.ValidationError,
    api.ApiValidationError,
}

KNOWN_EXCEPTIONS = DOWN_EXCEPTIONS | MUMBLE_EXCEPTIONS


class ErrorChecker:
    def __init__(self):
        self.verdict = Verdict.OK()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type in DOWN_EXCEPTIONS:
            self.verdict = Verdict.DOWN("Service is down")

        elif exc_type in MUMBLE_EXCEPTIONS:
            self.verdict = Verdict.MUMBLE("Incorrect http code or content")

        if exc_type:
            print(exc_type)
            print(exc_value.__dict__)
            traceback.print_tb(exc_traceback, file=sys.stdout)
            if exc_type not in KNOWN_EXCEPTIONS:
                raise exc_value

        return True


RESOURCE_COUNT = 3


@checker.define_check
async def check_service(request: CheckRequest) -> Verdict:
    with ErrorChecker() as ec:
        token_name = generators.gen_token_name()
        token_secret = api.issue_token(request.hostname, token_name)

        resources = {}
        for _ in range(RESOURCE_COUNT):
            resource_blob = generators.gen_resource_data()
            resources[api.create_resource(request.hostname, token_secret, resource_blob)] = resource_blob

        def _check_resources(token_secret_for_check):
            resource_ids = api.list_resources(request.hostname, token_secret_for_check)
            if len(resource_ids) != len(resources):
                ec.verdict = Verdict.MUMBLE("Incorrect resource ids: {}".format(resource_ids))
                return ec.verdict

            for resource_id in resource_ids:
                if resource_id not in resources:
                    ec.verdict = Verdict.MUMBLE("Incorrect resource_id: {}".format(resource_ids))
                    return ec.verdict

                actual_resource_blob = api.get_resource(request.hostname, token_secret_for_check, resource_id)
                if resources[resource_id] != actual_resource_blob:
                    print(f"Incorrect resource blob: {actual_resource_blob} != {resources[resource_id]}")
                    ec.verdict = Verdict.MUMBLE("Incorrect resource blob with id {}".format(resource_id))
                    return ec.verdict

        _check_resources(token_secret)

        another_token_name = generators.gen_token_name()
        another_token_secret = api.issue_token(request.hostname, another_token_name)

        zero_resource = sorted(resources.keys())[0]
        first_resource = sorted(resources.keys())[1]
        second_resource = sorted(resources.keys())[2]

        def _check_access():
            try:
                api.get_resource(request.hostname, another_token_secret, zero_resource)
                print("Get resource without access must raise an error")
                ec.verdict = Verdict.MUMBLE("Get resource without access must raise an error")
                return ec.verdict
            except HTTPError as e:
                if e.response.status_code != requests.codes.NOT_FOUND:
                    print(f"Incorrect http status code: {e.response.__dict__}")
                    ec.verdict = Verdict.MUMBLE(f"Incorrect http status code: {e.response.status_code}")
                    return ec.verdict

        _check_access()
        for resource_id in resources.keys():
            api.grant_access(request.hostname, token_secret, another_token_name, resource_id)

        _check_resources(another_token_secret)

        for _ in range(2):
            api.get_resource(request.hostname, another_token_secret, zero_resource)

        actual_stat = api.get_stat(request.hostname, another_token_secret)
        expected_stat = {
            zero_resource: 3,
            first_resource: 1,
            second_resource: 1,
        }
        if actual_stat != expected_stat:

            print("Invalid stat: {} != {}".format(actual_stat, expected_stat))
            ec.verdict = Verdict.MUMBLE(f"Invalid stat")
            return ec.verdict

        for resource_id in resources.keys():
            api.revoke_access(request.hostname, token_secret, another_token_name, resource_id)
            del expected_stat[resource_id]
            actual_stat = api.get_stat(request.hostname, another_token_secret)
            if actual_stat != expected_stat:
                print("Invalid stat: {} != {}".format(actual_stat, expected_stat))
                ec.verdict = Verdict.MUMBLE(f"Invalid stat")
                return ec.verdict

        _check_access()

        for ((static_category, static_name), expected_hash) in [
            # (["js", "swagger-ui-bundle.js"], "8e799858424d06ec280707ca0c1a81c07c42a221"),
            # (["js", "swagger-ui-standalone-preset.js"], "e35799828884129a0ae2f6bb570273ce150946a6"),
            # (["js", "swagger-initializer.js"], "23fd2279dffdc39c6463c0a0b64f2c0170398f6a"),
            (["css", "index.css"], "71586906338f69420aa4cf1d3494fee8c533f11a"),
            # (["css", "swagger-ui.css"], "bf63ba977691f9755b330a5f64a20289d6b38c86"),
        ]:
            if api.get_static_hash(request.hostname, static_category, static_name) != expected_hash:
                print(f"Invalid static content")
                ec.verdict = Verdict.MUMBLE(f"Invalid static content")

    return ec.verdict


@checker.define_vuln("Flag ID is the token's name, flag is the content of the resource")
class TokenoucerChecker(VulnChecker):
    @staticmethod
    def put(request: PutRequest) -> Verdict:
        with ErrorChecker() as ec:
            token_name = generators.gen_token_name()
            token_secret = api.issue_token(request.hostname, token_name)
            resource_id = api.create_resource(request.hostname, token_secret, request.flag)

            flag_id = json.dumps({
                'token_secret': token_secret,
                'resource_id': resource_id,
            })
            ec.verdict = Verdict.OK_WITH_FLAG_ID(token_name, flag_id)
        return ec.verdict

    @staticmethod
    def get(request: GetRequest) -> Verdict:
        with ErrorChecker() as ec:
            flag_id_json = json.loads(request.flag_id)
            token_secret = flag_id_json["token_secret"]
            resource_id = flag_id_json["resource_id"]

            try:
                resource_blob = api.get_resource(request.hostname, token_secret, resource_id)
                if resource_blob != request.flag:
                    print(f"corrupt flag: {resource_blob} != {request.flag}")
                    ec.verdict = Verdict.CORRUPT("corrupt flag")
                    return ec.verdict

            except requests.exceptions.HTTPError as e:
                print(f"corrupt flag, incorrect http code: {e.response.__dict__}")
                ec.verdict = Verdict.CORRUPT("corrupt flag, incorrect http code")
                return ec.verdict

        return ec.verdict


if __name__ == '__main__':
    checker.run()
