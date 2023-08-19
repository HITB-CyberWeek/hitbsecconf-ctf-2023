import base64
import functools

import requests
import jsonschema

import schemas

if os.getenv("DIRECT_CONNECT", False) == "True":
    PORT = 8080
    URL_PATTERN = "http://{hostname}:{port}/{method}"
else:
    PORT = 443
    URL_PATTERN = "https://{hostname}/{method}"


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
    url = URL_PATTERN.format(hostname=hostname, port=PORT, method=method)
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


def make_query_request(method, hostname, token_secret, result_key=None, params=None):
    url_with_method = URL_PATTERN.format(hostname=hostname, port=PORT, method=method)
    if params:
        url_parts = []
        for param_key, param_value in params.items():
            url_parts.append('{}={}'.format(param_key, param_value))
        url = url_with_method + '?' + '&'.join(url_parts)
    else:
        url = url_with_method

    headers = {
        'Authorization': 'Bearer ' + token_secret
    }
    r = requests.get(url, timeout=10, headers=headers)
    r.raise_for_status()
    json_res = r.json()
    if result_key:
        return json_res[result_key]
    return json_res


@with_validator(schemas.string_schema)
def issue_token(hostname, token_name):
    params = {
        'token_name': token_name
    }
    return make_json_request("/issue_token", hostname, result_key='token_secret', params=params)


@with_validator(schemas.string_schema)
def create_resource(hostname, token_secret, blob):
    params = {
        'blob': blob
    }
    return make_json_request("/create_resource", hostname, token_secret, 'resource_id', params)


@with_validator()
def grant_access(hostname, token_secret, token_name, resource_id):
    params = {
        'resource_id': resource_id,
        'token_name': token_name,
    }
    return make_json_request("/grant_access", hostname, token_secret, params=params)


@with_validator(schemas.string_schema)
def get_resource(hostname, token_secret, resource_id):
    params = {
        'resource_id': resource_id
    }
    return make_query_request("/get_resource", hostname, token_secret, 'blob', params)


@with_validator(schemas.string_list_schema)
def list_resources(hostname, token_secret):
    return make_query_request("/list_resources", hostname, token_secret, 'resource_ids')


@with_validator()
def revoke_access(hostname, token_secret, token_name, resource_id):
    params = {
        'token_name': token_name,
        'resource_id': resource_id,
    }
    return make_json_request("/revoke_access", hostname, token_secret, params=params)
