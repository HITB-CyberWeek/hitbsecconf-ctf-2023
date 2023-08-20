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

        def _check_access():
            try:
                api.get_resource(request.hostname, another_token_secret, sorted(resources.keys())[0])
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

        for resource_id in resources.keys():
            api.revoke_access(request.hostname, token_secret, another_token_name, resource_id)

        _check_access()

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
