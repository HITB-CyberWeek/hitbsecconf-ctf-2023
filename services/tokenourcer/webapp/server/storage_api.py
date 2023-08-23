import functools
import json
import random
import sys
import time
import uuid

import redis
from redis import WatchError


def with_pipe(handler):
    @functools.wraps(handler)
    def wrapped_handler(self, key, *args, **kwargs):
        for try_index in range(3):
            try:
                with self.redis_client.pipeline() as pipe:
                    pipe.watch(key)
                    res = handler(self, pipe, key, *args, **kwargs)
                    pipe.execute()
                    return res
            except WatchError:
                print(f'retry #{try_index + 1}', file=sys.stderr)
                time.sleep(2 ** try_index + random.random())
    return wrapped_handler


class StorageApi:
    def __init__(self, redis_client):
        self.redis_client: redis.Redis = redis_client

    @with_pipe
    def _append_value(self, pipe, key, field, element):
        list_data = pipe.hget(key, field)
        if not list_data:
            res = [element]
        else:
            res = json.loads(list_data) + [element]
        pipe.multi()
        pipe.hset(key, field, json.dumps(res))

    @with_pipe
    def _remove_value(self, pipe, key, field, element):
        list_data = pipe.hget(key, field)
        if list_data:
            res = json.loads(list_data)
            res.remove(element)
        else:
            raise KeyError(f'Invalid field {field} for key {key}')
        pipe.multi()
        pipe.hset(key, field, json.dumps(res))

    @with_pipe
    def _inc_value(self, pipe, key, field, element):
        full_key = "{}/{}".format(key, field)

        if not pipe.exists(full_key):
            raise KeyError(f'Invalid field {field} for key {key}')

        raw_value = pipe.hget(full_key, element)
        if raw_value:
            value = int(raw_value)
        else:
            value = 0
        value += 1
        pipe.multi()
        pipe.hset(full_key, element, str(value))

    @with_pipe
    def _del_value(self, pipe, key, field, element):
        full_key = "{}/{}".format(key, field)

        if not pipe.exists(full_key):
            raise KeyError(f'Invalid field {field} for key {key}')

        pipe.multi()
        pipe.hdel(full_key, element)

    def add_resource(self, blob):
        resource_id = uuid.uuid4().hex
        self.redis_client.hset("resources", resource_id, blob)
        return resource_id

    def get_resource(self, resource_id):
        res = self.redis_client.hget("resources", resource_id)
        if res:
            return res.decode()
        return None

    def add_token(self, token_name, token_secret):
        self.redis_client.hset("tokens", token_name, token_secret)
        self.redis_client.hset("token_secrets", token_secret, '1')

    def get_token_secret(self, token_name):
        res = self.redis_client.hget("tokens", token_name)
        if res:
            return res.decode()
        return None

    def is_token_exist(self, token_name):
        return self.redis_client.hexists("tokens", token_name)

    def is_token_secret_exist(self, token_secret):
        return self.redis_client.hexists("token_secrets", token_secret)

    def add_resource_to_token(self, resource_id, token_secret):
        self._append_value("resource_to_tokens", resource_id, token_secret, )

    def get_tokens_by_resource_id(self, resource_id):
        raw_tokens = self.redis_client.hget("resource_to_tokens", resource_id)
        if raw_tokens:
            return json.loads(raw_tokens)
        return []

    def remove_resource_to_token(self, resource_id, token_secret):
        self._remove_value("resource_to_tokens", resource_id, token_secret)

    def add_token_to_resource(self, token_secret, resource_id):
        self._append_value("token_to_resources", token_secret, resource_id)

    def get_resource_ids_by_token(self, token_secret, redis_client=None):
        raw_resource_ids = (redis_client or self.redis_client).hget("token_to_resources", token_secret)
        if raw_resource_ids:
            return set(json.loads(raw_resource_ids))
        return set()

    @staticmethod
    def _get_counter_full_key(token_secret):
        return "counter/{}".format(token_secret)

    def get_stat(self, token_secret):
        full_key = self._get_counter_full_key(token_secret)
        resource_ids = [r_id.decode() for r_id in self.redis_client.hkeys(full_key)]
        return {resource_id: int(self.redis_client.hget(full_key, resource_id).decode()) for resource_id in resource_ids}

    def create_counter(self, token_secret, resource_id):
        full_key = self._get_counter_full_key(token_secret)
        with self.redis_client.pipeline() as pipe:
            pipe.watch(full_key)
            value = pipe.hget(full_key, resource_id)
            if not value:
                pipe.multi()
                pipe.hset(full_key, resource_id, "0")
            pipe.execute()

    def inc_counter(self, token_secret, resource_id):
        self._inc_value("counter", token_secret, resource_id)

    def del_counter(self, token_secret, resource_id):
        self._del_value("counter", token_secret, resource_id)

    def remove_token_to_resource(self, token_secret, resource_id):
        with self.redis_client.pipeline() as pipe:
            pipe.watch("token_to_resources")
            resource_ids = self.get_resource_ids_by_token(token_secret, pipe)
            pipe.multi()
            if len(resource_ids) == 1:
                pipe.hdel("token_to_resources", token_secret)
                pipe.delete(self._get_counter_full_key(token_secret))
            else:
                resource_ids.remove(resource_id)
                pipe.hset("token_to_resources", token_secret, json.dumps(list(resource_ids)))
                pipe.hdel(self._get_counter_full_key(token_secret), resource_id)

            pipe.execute()
