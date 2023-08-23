import functools

from flask import Flask, request, make_response, redirect
import redis

import util
from storage_api import StorageApi
from config import get_config

storage_api = StorageApi(redis.Redis(host=get_config().redis_host))


app = Flask(__name__)


def handler_wrapper(handler):
    @functools.wraps(handler)
    def wrapped_handler(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except ParamError:
            return make_response("invalid params", 400)
    return wrapped_handler


def with_auth_token(handler):
    @functools.wraps(handler)
    def wrapped_handler(*args, **kwargs):
        if not request.authorization:
            return make_response('bearer token is required for this request', 401)

        if not storage_api.is_token_secret_exist(request.authorization.token):
            return make_response('not found', 404)

        return handler(request.authorization.token, *args, **kwargs)
    return wrapped_handler


class ParamError(Exception):
    pass


def get_json_param(name):
    data = request.get_json()
    if name not in data:
        raise ParamError
    return data[name]


def get_query_param(name):
    data = request.args
    if name not in data:
        raise ParamError
    return data[name]


@app.post('/issue_token')
@handler_wrapper
def issue_token():
    token_name = get_json_param('token_name')
    if storage_api.is_token_exist(token_name):
        return make_response("token name is already exist", 400)

    token_secret = token_name + ':' + util.gen_token_secret()
    storage_api.add_token(token_name, token_secret)

    return {
        'token_secret': token_secret
    }


@app.post('/create_resource')
@handler_wrapper
@with_auth_token
def create_resource(token_secret):
    blob = get_json_param('blob')
    resource_id = storage_api.add_resource(blob)

    storage_api.add_resource_to_token(resource_id, token_secret)

    storage_api.add_token_to_resource(token_secret, resource_id)

    storage_api.create_counter(token_secret, resource_id)

    return {
        'resource_id': resource_id
    }


@app.post('/grant_access')
@handler_wrapper
@with_auth_token
def grant_access(owner_token_secret):
    resource_id = get_json_param('resource_id')
    token_name = get_json_param('token_name')

    access_tokens = storage_api.get_tokens_by_resource_id(resource_id)
    if not access_tokens or access_tokens[0] != owner_token_secret:
        return make_response('resource not found', 404)

    token_secret = storage_api.get_token_secret(token_name)
    if not token_secret:
        return make_response('token not found', 404)

    storage_api.add_resource_to_token(resource_id, token_secret)
    storage_api.add_token_to_resource(token_secret, resource_id)

    storage_api.create_counter(token_secret, resource_id)
    return {}


@app.post('/revoke_access')
@handler_wrapper
@with_auth_token
def revoke_access(owner_token_secret):
    token_name = get_json_param('token_name')
    resource_id = get_json_param('resource_id')

    access_tokens = storage_api.get_tokens_by_resource_id(resource_id)
    if not access_tokens or access_tokens[0] != owner_token_secret:
        return make_response('resource not found', 404)

    token_secret = storage_api.get_token_secret(token_name)
    if not token_secret:
        return make_response('token not found', 404)

    if token_secret not in storage_api.get_tokens_by_resource_id(resource_id):
        return make_response('access is already absent', 400)

    storage_api.remove_resource_to_token(resource_id, token_secret)
    storage_api.remove_token_to_resource(token_secret, resource_id)
    return {}


@app.get('/get_resource')
@handler_wrapper
@with_auth_token
def get_resource(token_secret):
    resource_id = get_query_param('resource_id')
    if token_secret not in storage_api.get_tokens_by_resource_id(resource_id):
        return make_response('resource not found', 404)

    resource = storage_api.get_resource(resource_id)
    if not resource:
        return make_response('resource not found', 404)
    storage_api.inc_counter(token_secret, resource_id)
    return {
        'blob': resource
    }


@app.get('/list_resources')
@handler_wrapper
@with_auth_token
def list_resources(token_secret):
    resource_ids = list(storage_api.get_resource_ids_by_token(token_secret) or [])

    return {
        'resource_ids': resource_ids,
    }


@app.get('/get_stat')
@handler_wrapper
@with_auth_token
def get_stat(token_secret):
    stat = storage_api.get_stat(token_secret)

    return {
        'stat': stat,
    }


@app.get('/')
def index_handler():
    return redirect("/index.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
