import os
import sys

import peewee

from playhouse.postgres_ext import JSONField

import config

service_config = config.get_config()
pg_db = peewee.PostgresqlDatabase(service_config.postgres_db, user=service_config.postgres_user, password=service_config.postgres_password, host=service_config.postgres_host, port=5432)


class BaseModel(peewee.Model):
    class Meta:
        database = pg_db


class TokenModel(BaseModel):
    data = peewee.CharField()


class ResourceModel(BaseModel):
    id = peewee.AutoField()
    data = peewee.BlobField()
    hex_hash = peewee.CharField()
    name = peewee.CharField()


class UserModel(BaseModel):
    username = peewee.CharField(primary_key=True)
    password_hash = peewee.CharField()


class UserTokensModel(BaseModel):
    username = peewee.ForeignKeyField(UserModel)
    token = peewee.CharField()


class AccessMapModel(BaseModel):
    username = peewee.ForeignKeyField(UserModel, index=True)
    token_to_resources = JSONField()
    resource_to_tokens = JSONField()


class ForeignResources(BaseModel):
    username = peewee.ForeignKeyField(UserModel, index=True)
    token = peewee.CharField()
    resource_id = peewee.ForeignKeyField(ResourceModel)


def init():
    print('Init tables', file=sys.stderr)
    pg_db.connect()
    pg_db.create_tables([TokenModel, ResourceModel, UserModel, UserTokensModel, AccessMapModel, ForeignResources])
