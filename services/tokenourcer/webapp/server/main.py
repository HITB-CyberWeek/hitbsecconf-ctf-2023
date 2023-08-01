import redis
from flask import Flask, request, make_response

import db_api
from session_manager import SessionManager

app = Flask(__name__)
redis_conn = redis.Redis(host='redis')
sm = SessionManager(redis_conn)


@app.post('/register')
def register_handler():
    data = request.get_json()
    username = data['username']
    password = data['password']

    user = db_api.create_user(username, password)
    secret = sm.create(username)

    response = make_response('{}')
    response.set_cookie('secret', secret)
    response.set_cookie('username', username)
    return response


@app.post('/login')
def login_handler():
    data = request.get_json()
    username = data['username']
    password = data['password']

    is_valid_user_pair = db_api.validate_user_pair(username, password)
    if is_valid_user_pair:
        secret = sm.create(username)

        response = make_response('{}')
        response.set_cookie('secret', secret)
        response.set_cookie('username', username)
        return response
    else:
        response = make_response('invalid user pair')
        response.status_code = 400
        return response


@app.post('/issue_token')
def issue_token_handler():
    username = request.cookies.get('username')
    secret = request.cookies.get('secret')
    if not username or not secret:
        return make_response('invalid cookies', 401)

    if not sm.validate(username, secret):
        return make_response('invalid cookies', 401)

    token = db_api.issue_token(username)
    return make_response({'token': token})


@app.post('/create_resource')
def create_resource_handler():
    username = request.cookies.get('username')
    secret = request.cookies.get('secret')
    if not username or not secret:
        return make_response('invalid cookies', 401)

    if not sm.validate(username, secret):
        return make_response('invalid cookies', 401)

    data = request.get_json()
    token = data['token']
    blob = data['blob']

    if not db_api.validate_user_token(username, token):
        return make_response('token not found', 404)

    resource_id = db_api.create_resource(username, token, blob)
    return make_response({'resource_id': resource_id})


@app.get('/get_resource')
def get_resource_handler():
    username = request.args.get('username')
    token = request.args.get('token')
    resource_id = request.args.get('resource_id')

    resource_data = db_api.get_resource(username, token, resource_id)
    if not resource_data:
        return make_response('resource not found', 404)

    return make_response({
        'blob': bytes(resource_data).decode()
    })


@app.post('/grant_access')
def grant_access_handler():
    username = request.cookies.get('username')
    secret = request.cookies.get('secret')
    if not username or not secret:
        return make_response('invalid cookies', 401)

    if not sm.validate(username, secret):
        return make_response('invalid cookies', 401)

    data = request.get_json()
    username = username or data['username']
    token = data['token']
    resource_id = data['resource_id']

    db_api.grant_access(username, token, resource_id)

    return make_response({})


@app.post('/remove_resource')
def remove_resource_handler():
    username = request.cookies.get('username')
    secret = request.cookies.get('secret')
    if not username or not secret:
        return make_response('invalid cookies', 401)

    if not sm.validate(username, secret):
        return make_response('invalid cookies', 401)

    data = request.get_json()
    username = data['username']
    token = data['token']
    resource_id = data['resource_id']

    resource_data = db_api.get_resource(username, token, resource_id)
    if not resource_data:
        return make_response('resource not found', 404)

    db_api.remove_resource(username, resource_id)

    return make_response({})


@app.get('/list_resources')
def list_resources_handler():
    username = request.cookies.get('username')
    secret = request.cookies.get('secret')
    if not username or not secret:
        return make_response('invalid cookies', 401)

    if not sm.validate(username, secret):
        return make_response('invalid cookies', 401)

    resources = db_api.list_resources(username)

    return make_response({'resources': resources})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
