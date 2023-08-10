import random
import sys

import peewee

import models
import util


class DBApiError(Exception):
    pass


def create_user(username, password):
    user_exists = models.UserModel.select().where(models.UserModel.username == username).exists()
    if user_exists:
        raise DBApiError('User is already exist')

    user = models.UserModel.create(username=username, password_hash=util.base_hash(password))
    models.AccessMapModel.create(username=username, token_to_resources={}, resource_to_tokens={})
    return user


def validate_user_pair(username, password):
    try:
        user = models.UserModel.get(models.UserModel.username == username)
        return user.password_hash == util.base_hash(password)
    except peewee.DoesNotExist:
        return False


def do_smth(username):
    token0 = issue_token(username)
    token1 = issue_token(username)

    resource0 = create_resource(username, token0, 'some resource_name', b'some data')
    resource1 = create_resource(username, token1, 'some resource_name', b'some data')
    resource2 = create_resource(username, token1, 'some resource_name', b'some data')


def issue_token(username):
    token = models.TokenModel.create(data=util.gen_str()).data
    models.UserTokensModel.create(username=username, token=token)

    access_map = models.AccessMapModel.get(models.AccessMapModel.username == username)
    access_map.token_to_resources[token] = []
    models.AccessMapModel.bulk_update([access_map], fields=['token_to_resources'])

    return token


def validate_user_token(username, token):
    try:
        models.UserTokensModel.get(models.UserTokensModel.username == username, models.UserTokensModel.token == token)
        return True
    except peewee.DoesNotExist:
        return False


def create_resource(username, token, name, resource_data):
    hex_hash = util.get_hex_hash(resource_data)
    resource = models.ResourceModel.create(data=resource_data, hex_hash=hex_hash, name=name)
    resource_id = str(resource.id)

    with models.pg_db.atomic():
        access_map = models.AccessMapModel.get(models.AccessMapModel.username == username)
        if token not in access_map.token_to_resources:
            access_map.token_to_resources[token] = []
        if resource_id not in access_map.resource_to_tokens:
            access_map.resource_to_tokens[resource_id] = []

        access_map.token_to_resources[token].append(resource_id)
        access_map.resource_to_tokens[resource_id].append(token)

        models.AccessMapModel.bulk_update([access_map], fields=['token_to_resources', 'resource_to_tokens'])
    print(access_map.token_to_resources, file=sys.stderr)
    return resource_id


def list_resources(username):
    access_map = models.AccessMapModel.get(models.AccessMapModel.username == username)
    user_tokens = [ut.token for ut in models.UserTokensModel.select().where(models.UserTokensModel.username == username)]

    resource_ids = {resource_id for user_token in user_tokens for resource_id in access_map.token_to_resources[user_token]}
    return [{
        'id': res.id,
        'name': res.name,
        'hex_hash': res.hex_hash,
    } for res in models.ResourceModel.select().where(models.ResourceModel.id.in_(resource_ids))]


def list_resources_by_token(username, token):
    access_map = models.AccessMapModel.get(models.AccessMapModel.username == username)

    print(repr(access_map.resource_to_tokens), access_map.resource_to_tokens, file=sys.stderr)
    print(repr(token), token, file=sys.stderr)

    print(repr(access_map.resource_to_tokens), access_map.resource_to_tokens)
    print(repr(token), token)

    resource_ids = [r_id for r_id, tokens in access_map.resource_to_tokens.items() if token in tokens]

    return [{
        'id': res.id,
        'name': res.name,
        'hex_hash': res.hex_hash,
    } for res in models.ResourceModel.select().where(models.ResourceModel.id.in_(resource_ids))]


def list_user_tokens(username):
    return [ut.token for ut in models.UserTokensModel.select().where(models.UserTokensModel.username == username)]


def check_access_map(access_map: models.AccessMapModel):
    assert access_map.token_to_resources.keys() == {rtt for user_token in access_map.resource_to_tokens.values() for rtt in user_token}
    assert access_map.resource_to_tokens.keys() == {ttr for resource_ids in access_map.token_to_resources.values() for ttr in resource_ids}


def remove_resource(username, resource_id):
    resource_id = str(resource_id)

    access_map = models.AccessMapModel.get(models.AccessMapModel.username == username)

    if resource_id in access_map.resource_to_tokens:
        tokens = list(access_map.resource_to_tokens[resource_id])
        del access_map.resource_to_tokens[resource_id]
        for token in tokens:
            del access_map.token_to_resources[token]

        models.AccessMapModel.bulk_update([access_map], fields=['token_to_resources', 'resource_to_tokens'])

        check_access_map(access_map)

        revoke_user_tokens(username, tokens)
        resource = models.ResourceModel.get(models.ResourceModel.id == resource_id)
        resource.delete_instance()


def grant_access(username, token, resource_id):
    resource_id = str(resource_id)
    access_map = models.AccessMapModel.get(models.AccessMapModel.username == username)

    if resource_id in access_map.resource_to_tokens:
        access_map.resource_to_tokens[resource_id].append(token)

    if token in access_map.token_to_resources:
        access_map.token_to_resources[token].append(resource_id)

    models.AccessMapModel.bulk_update([access_map], fields=['token_to_resources', 'resource_to_tokens'])


def revoke_user_tokens(username, tokens):
    for utm in models.UserTokensModel.select().where(models.UserTokensModel.username == username, models.UserTokensModel.token.in_(tokens)):
        utm.delete_instance()


def get_resource(username, token, resource_id):
    resource_id = str(resource_id)
    access_map = models.AccessMapModel.get(models.AccessMapModel.username == username)
    if token in access_map.token_to_resources and resource_id in access_map.token_to_resources[token]:
        return models.ResourceModel.get(models.ResourceModel.id == resource_id).data

    return None


def is_resource_exist(username, resource_id):
    return str(resource_id) in {str(r['id']) for r in list_resources(username)}


# def main():
#     user0 = create_user('username{}'.format(random.randint(1, 1000)), 'password')
#     user1 = create_user('username{}'.format(random.randint(1, 1000)), 'password')
#
#     token0 = issue_token(user0.username)
#     token1 = issue_token(user0.username)
#
#     resource0 = create_resource(user0.username, token0, 'resource_name', b'some data')
#     resource1 = create_resource(user0.username, token0, 'resource_name', b'some data')
#     resource2 = create_resource(user0.username, token1, 'resource_name', b'some data')
#
#     username = user0.username
#     print(username)
#
#     resource_ids = list_resources(username)
#     print(resource_ids)
#
#     access_map = models.AccessMapModel.get(models.AccessMapModel.username == username)
#     print(access_map.__dict__)
#
#     grant_access(username, 'ne-token', resource0)
#
#     try:
#         remove_resource(username, resource_ids[-1])
#     except Exception:
#         pass
#
#     resource_ids = list_resources(username)
#     print(resource_ids)
#
#     r = get_resource(user0.username, token0, resource1)
#     print(r.__dict__)
#
#     models.pg_db.close()
#
#
# if __name__ == '__main__':
#     main()
