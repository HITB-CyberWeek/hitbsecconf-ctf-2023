import base64
import requests

PORT = 8080
URL_PATTERN = "http://{hostname}:{port}/{method}"


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
    json_res = r.json()
    if result_key:
        return json_res[result_key]
    return json_res


def issue_token(hostname, token_name):
    params = {
        'token_name': token_name
    }
    return make_json_request("/issue_token", hostname, result_key='token_secret', params=params)


def create_resource(hostname, token_secret, blob):
    params = {
        'blob': blob
    }
    return make_json_request("/create_resource", hostname, token_secret, 'resource_id', params)


def grant_access(hostname, token_secret, token_name, resource_id):
    params = {
        'resource_id': resource_id,
        'token_name': token_name,
    }
    return make_json_request("/grant_access", hostname, token_secret, params=params)


def get_resource(hostname, token_secret, resource_id):
    params = {
        'resource_id': resource_id
    }
    return make_query_request("/get_resource", hostname, token_secret, 'blob', params)


def revoke_access(hostname, token_secret, token_name, resource_id):
    params = {
        'token_name': token_name,
        'resource_id': resource_id,
    }
    return make_json_request("/revoke_access", hostname, token_secret, params=params)
