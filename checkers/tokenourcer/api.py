import functools
import hashlib
import os

import requests
import jsonschema

import schemas

if os.getenv("DIRECT_CONNECT", False):
    PORT = 8080
    URL_SCHEMA = "http"

else:
    PORT = 443
    URL_SCHEMA = "https"


API_REQUEST_URL_PATTERN = "%s://{hostname}:{port}/{method}" % URL_SCHEMA
STATIC_REQUEST_URL_PATTERN = "%s://{hostname}:{port}/assets/{category}/{name}" % URL_SCHEMA


class ApiValidationError(Exception):
    pass


def with_validator(schema=None):
    def _validator_wrapper(handler):
        @functools.wraps(handler)
        def validator_wrapper(*args, **kwargs):
            try:
                res = handler(*args, **kwargs)
                if schema:
                    jsonschema.validate(res, schema)
                return res
            except KeyError as e:
                raise ApiValidationError(e)
        return validator_wrapper
    return _validator_wrapper


def make_json_request(method, hostname, token_secret=None, result_key=None, params=None):
    url = API_REQUEST_URL_PATTERN.format(hostname=hostname, port=PORT, method=method)
    kwargs = {
        'timeout': 10,
        'json': params or {}
    }
    if token_secret:
        kwargs['headers'] = {
            'Authorization': 'Bearer ' + token_secret
        }
    r = requests.post(url, **kwargs)
    r.raise_for_status()
    json_res = r.json()
    if result_key:
        return json_res[result_key]
    return json_res


def make_query_request(method, hostname, token_secret=None, result_key=None, params=None):
    url_with_method = API_REQUEST_URL_PATTERN.format(hostname=hostname, port=PORT, method=method)
    if params:
        url_parts = []
        for param_key, param_value in params.items():
            url_parts.append('{}={}'.format(param_key, param_value))
        url = url_with_method + '?' + '&'.join(url_parts)
    else:
        url = url_with_method

    kwargs = {
        'timeout': 10
    }
    if token_secret:
        kwargs['headers'] = {
            'Authorization': 'Bearer ' + token_secret
        }
    r = requests.get(url, **kwargs)
    r.raise_for_status()
    json_res = r.json()
    if result_key:
        return json_res[result_key]
    return json_res


def get_hex_hash(data):
    hasher = hashlib.sha1()
    hasher.update(data)
    return hasher.hexdigest()


def get_static_hash(hostname, category, name):
    url = STATIC_REQUEST_URL_PATTERN.format(hostname=hostname, port=PORT, category=category, name=name)
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return get_hex_hash(r.content)


@with_validator(schemas.string_schema)
def issue_token(hostname, token_name):
    params = {
        'token_name': token_name
    }
    return make_json_request("issue_token", hostname, result_key='token_secret', params=params)


@with_validator(schemas.string_schema)
def create_resource(hostname, token_secret, blob):
    params = {
        'blob': blob
    }
    return make_json_request("create_resource", hostname, token_secret, 'resource_id', params)


@with_validator()
def grant_access(hostname, token_secret, token_name, resource_id):
    params = {
        'resource_id': resource_id,
        'token_name': token_name,
    }
    return make_json_request("grant_access", hostname, token_secret, params=params)


@with_validator(schemas.string_schema)
def get_resource(hostname, token_secret, resource_id):
    params = {
        'resource_id': resource_id
    }
    return make_query_request("get_resource", hostname, token_secret, 'blob', params)


@with_validator(schemas.string_list_schema)
def list_resources(hostname, token_secret):
    return make_query_request("list_resources", hostname, token_secret, 'resource_ids')


@with_validator(schemas.stat_dict_schema)
def get_stat(hostname, token_secret):
    return make_query_request("get_stat", hostname, token_secret, 'stat')


@with_validator()
def revoke_access(hostname, token_secret, token_name, resource_id):
    params = {
        'token_name': token_name,
        'resource_id': resource_id,
    }
    return make_json_request("revoke_access", hostname, token_secret, params=params)
