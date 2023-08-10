import base64
import functools
import os
import sys
from sys import stderr

import redis
from flask import Flask, request, make_response, render_template, redirect
import config
import inspect
import db_api
from session_manager import SessionManager

app = Flask(__name__)
service_config = config.get_config()
redis_conn = redis.Redis(host=service_config.redis_host)
sm = SessionManager(redis_conn)


def with_auth(redirect_url=None):
    if redirect_url:
        response_getter = lambda: redirect(redirect_url)
    else:
        response_getter = lambda: make_response('invalid cookies', 401)

    def with_auth_inner(handler):
        @functools.wraps(handler)
        def wrapped_handler():
            username = request.cookies.get('username')
            secret = request.cookies.get('secret')
            if not username or not secret:
                return response_getter()

            if not sm.validate(username, secret):
                return response_getter()
            return handler(username)

        return wrapped_handler
    return with_auth_inner


def handler_wrapper(handler):
    @functools.wraps(handler)
    def wrapped_handler(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except (ParamError, AssertionError):
            return make_response("invalid params", 400)
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


@app.post('/register')
@handler_wrapper
def register_handler():
    username = get_json_param('username', )
    password = get_json_param('password', )

    db_api.create_user(username, password)
    secret = sm.create(username)

    response = make_response('{}')
    response.set_cookie('secret', secret)
    response.set_cookie('username', username)
    return response


@app.post('/login')
@handler_wrapper
def login_handler():
    username = get_json_param('username')
    password = get_json_param('password')

    is_valid_user_pair = db_api.validate_user_pair(username, password)
    if is_valid_user_pair:
        secret = sm.create(username)

        response = make_response('{}')
        response.set_cookie('secret', secret)
        response.set_cookie('username', username)

        db_api.do_smth(username)

        return response
    else:
        response = make_response('invalid user pair')
        response.status_code = 400
        return response


@app.post('/issue_token')
@with_auth()
def issue_token_handler(username):
    token = db_api.issue_token(username)
    return make_response({'token': token})


@app.post('/create_resource')
@with_auth()
@handler_wrapper
def create_resource_handler(username):
    name = get_json_param('name')
    token = get_json_param('token')
    b64blob = get_json_param('b64blob')

    blob = base64.b64decode(b64blob)

    if not db_api.validate_user_token(username, token):
        return make_response('token not found', 404)

    resource_id = db_api.create_resource(username, token, name, blob)
    return make_response({'resource_id': resource_id})


@app.get('/get_resource')
@handler_wrapper
def get_resource_handler():
    username = get_query_param('username')
    token = get_query_param('token')
    resource_id = get_query_param('resource_id')

    resource_data = db_api.get_resource(username, token, resource_id)
    if not resource_data:
        return make_response('resource not found', 404)

    return make_response({
        'blob': bytes(resource_data).decode()
    })


@app.post('/grant_access')
@with_auth()
@handler_wrapper
def grant_access_handler(username):
    username = get_json_param('username')
    token = get_json_param('token')
    resource_id = get_json_param('resource_id')

    db_api.grant_access(username, token, resource_id)

    return make_response({})


@app.post('/remove_resource')
@with_auth()
@handler_wrapper
def remove_resource_handler(username):
    username = get_json_param('username')
    resource_id = get_json_param('resource_id')

    if not db_api.is_resource_exist(username, resource_id):
        return make_response('resource not found', 404)

    db_api.remove_resource(username, resource_id)

    return make_response({})


@app.get('/list_resources')
@with_auth()
def list_resources_handler(username):
    resources = db_api.list_resources(username)

    return make_response({'resources': resources})


@app.get('/list_resources_by_token')
@handler_wrapper
def list_resources_by_token_handler():
    username = get_query_param('username')
    token = get_query_param('token')

    resources = db_api.list_resources_by_token(username, token)

    return make_response({'resources': resources})


@app.get('/register_page')
def register_page_handler():
    return render_template('auth.html', action='Register')


@app.get('/login_page')
def login_page_handler():
    return render_template('auth.html', action='Login')


@app.get('/')
@with_auth('/login_page')
def index_page_handler(username):
    resources = db_api.list_resources(username)
    data = {
        'username': username,
        'resources': resources,
    }

    return render_template('index.html', **data)


@app.get('/create_resource_page')
@with_auth('/login_page')
def create_resource_page_handler(username):
    tokens = db_api.list_user_tokens(username)
    return render_template('create_resource.html', tokens=tokens)


@app.get('/get_resource_page')
@with_auth('/login_page')
def get_resource_page_handler(username):
    return render_template('get_resource.html')


@app.get('/tokens_page')
@with_auth('/login_page')
def tokens_page_handler(username):
    tokens = db_api.list_user_tokens(username)
    return render_template('tokens.html', tokens=tokens)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
