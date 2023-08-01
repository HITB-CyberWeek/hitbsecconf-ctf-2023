import random

import peewee


from playhouse.postgres_ext import JSONField

import util

pg_db = peewee.PostgresqlDatabase('postgres', user='postgres', password='mysecretpassword', host='postgres', port=5432)


class DBApiError(Exception):
    pass


class BaseModel(peewee.Model):
    class Meta:
        database = pg_db


class TokenModel(BaseModel):
    data = peewee.CharField()


class ResourceModel(BaseModel):
    id = peewee.AutoField()
    data = peewee.BlobField()


class UserModel(BaseModel):
    username = peewee.CharField(primary_key=True)
    password_hash = peewee.CharField()


class UserTokensModel(BaseModel):
    username = peewee.ForeignKeyField(UserModel)
    token = peewee.CharField(index=True)


class AccessMapModel(BaseModel):
    username = peewee.ForeignKeyField(UserModel, index=True)
    token_to_resources = JSONField()
    resource_to_tokens = JSONField()


pg_db.connect()
pg_db.create_tables([TokenModel, ResourceModel, UserModel, UserTokensModel, AccessMapModel])


def create_user(username, password):
    user_exists = UserModel.select().where(UserModel.username == username).exists()
    if user_exists:
        raise DBApiError('User is already exist')

    user = UserModel.create(username=username, password_hash=util.base_hash(password))
    AccessMapModel.create(username=user.username, token_to_resources={}, resource_to_tokens={})
    return user


def validate_user_pair(username, password):
    try:
        user = UserModel.get(UserModel.username == username)
        return user.password_hash == util.base_hash(password)
    except peewee.DoesNotExist:
        return False


def issue_token(username):
    token = TokenModel.create(data=util.gen_str()).data
    UserTokensModel.create(username=username, token=token)

    access_map = AccessMapModel.get(AccessMapModel.username == username)
    access_map.token_to_resources[token] = []
    AccessMapModel.bulk_update([access_map], fields=['token_to_resources'])

    return token


def validate_user_token(username, token):
    try:
        UserTokensModel.get(UserTokensModel.username == username, UserTokensModel.token == token)
        return True
    except peewee.DoesNotExist:
        return False


def create_resource(username, token, resource_data):
    resource = ResourceModel.create(data=resource_data)
    resource_id = str(resource.id)

    with pg_db.atomic():
        access_map = AccessMapModel.get(AccessMapModel.username == username)
        if token not in access_map.token_to_resources:
            access_map.token_to_resources[token] = []
        if resource_id not in access_map.resource_to_tokens:
            access_map.resource_to_tokens[resource_id] = []

        access_map.token_to_resources[token].append(resource_id)
        access_map.resource_to_tokens[resource_id].append(token)

        AccessMapModel.bulk_update([access_map], fields=['token_to_resources', 'resource_to_tokens'])
    return resource_id


def list_resources(username):
    access_map = AccessMapModel.get(AccessMapModel.username == username)
    user_tokens = [ut.token for ut in UserTokensModel.select().where(UserTokensModel.username == username)]

    return list({ut for user_token in user_tokens for ut in access_map.token_to_resources[user_token]})


def check_access_map(access_map: AccessMapModel):
    assert access_map.token_to_resources.keys() == {rtt for user_token in access_map.resource_to_tokens.values() for rtt in user_token}
    assert access_map.resource_to_tokens.keys() == {ttr for resource_ids in access_map.token_to_resources.values() for ttr in resource_ids}


def remove_resource(username, resource_id):
    resource_id = str(resource_id)

    access_map = AccessMapModel.get(AccessMapModel.username == username)

    if resource_id in access_map.resource_to_tokens:
        tokens = list(access_map.resource_to_tokens[resource_id])
        del access_map.resource_to_tokens[resource_id]
        for token in tokens:
            del access_map.token_to_resources[token]

        AccessMapModel.bulk_update([access_map], fields=['token_to_resources', 'resource_to_tokens'])

        check_access_map(access_map)

        revoke_user_tokens(username, tokens)


def grant_access(username, token, resource_id):
    resource_id = str(resource_id)
    access_map = AccessMapModel.get(AccessMapModel.username == username)

    if resource_id in access_map.resource_to_tokens:
        access_map.resource_to_tokens[resource_id].append(token)

    if token in access_map.token_to_resources:
        access_map.token_to_resources[token].append(resource_id)

    AccessMapModel.bulk_update([access_map], fields=['token_to_resources', 'resource_to_tokens'])


def revoke_user_tokens(username, tokens):
    for utm in UserTokensModel.select().where(UserTokensModel.username == username, UserTokensModel.token.in_(tokens)):
        utm.delete_instance()


def get_resource(username, token, resource_id):
    resource_id = str(resource_id)
    access_map = AccessMapModel.get(AccessMapModel.username == username)
    if token in access_map.token_to_resources and resource_id in access_map.token_to_resources[token]:
        return ResourceModel.get(ResourceModel.id == resource_id).data

    return None


def main():
    # pg_db.connect()
    pg_db.create_tables([TokenModel, ResourceModel, UserModel, UserTokensModel, AccessMapModel])

    user0 = create_user('username{}'.format(random.randint(1, 1000)), 'password')
    user1 = create_user('username{}'.format(random.randint(1, 1000)), 'password')

    token0 = issue_token(user0.username)
    token1 = issue_token(user0.username)

    resource0 = create_resource(user0.username, token0, b'some data')
    resource1 = create_resource(user0.username, token0, b'some data')
    resource2 = create_resource(user0.username, token1, b'some data')

    username = user0.username
    print(username)

    resource_ids = list_resources(username)
    print(resource_ids)

    access_map = AccessMapModel.get(AccessMapModel.username == username)
    print(access_map.__dict__)

    grant_access(username, 'ne-token', resource0)

    try:
        remove_resource(username, resource_ids[-1])
    except Exception:
        pass

    resource_ids = list_resources(username)
    print(resource_ids)

    r = get_resource(user0.username, token0, resource1)
    print(r.__dict__)

    pg_db.close()


if __name__ == '__main__':
    main()
