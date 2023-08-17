import dataclasses
import functools
import json
import uuid

import redis


def with_pipe(handler):
    @functools.wraps(handler)
    def wrapped_handler(self, key, *args, **kwargs):
        with self.redis_client.pipeline() as pipe:
            pipe.watch(key)
            res = handler(self, pipe, key, *args, **kwargs)
            pipe.execute()
            return res
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
        if not list_data:
            res = [element]
        else:
            res = json.loads(list_data) + [element]
        pipe.multi()
        pipe.hset(key, field, json.dumps(res))

    @with_pipe
    def _inc_value(self, pipe, key, field, element):
        raw_value = pipe.hget(key, field)
        if raw_value:
            value = json.loads(raw_value)
            if element not in value:
                value[element] = 0
            value[element] += 1
        else:
            raise KeyError(f'Invalid field {field} for key {key}')
        pipe.multi()
        pipe.hset(key, field, json.dumps(value))

    @with_pipe
    def _del_value(self, pipe, key, field, element):
        raw_value = pipe.hget(key, field)
        pipe.multi()
        if raw_value:
            value = json.loads(raw_value)
            del value[element]
            pipe.hset(key, field, json.dumps(value))
        else:
            raise KeyError(f'Invalid field {field} for key {key}')
        pipe.hset(key, field, json.dumps(value))

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
        self._append_value("token_to_resource", token_secret, resource_id)

    @staticmethod
    def get_resource_ids_by_token(pipe, token_secret):
        raw_resource_ids = pipe.hget("token_to_resource", token_secret)
        if raw_resource_ids:
            return set(json.loads(raw_resource_ids))
        return set()

    def create_counter(self, token_secret, resource_id):
        self.redis_client.hset("counter", token_secret, json.dumps({resource_id: 0}))

    def inc_counter(self, token_secret, resource_id):
        self._inc_value("counter", token_secret, resource_id)

    def del_counter(self, token_secret, resource_id):
        self._del_value("counter", token_secret, resource_id)

    def remove_token_to_resource(self, token_secret, resource_id):
        with self.redis_client.pipeline() as pipe:
            pipe.watch("token_to_resource", "counter")
            resource_ids = self.get_resource_ids_by_token(pipe, token_secret)
            raw_counter = pipe.hget("counter", token_secret)
            pipe.multi()
            if len(resource_ids) == 1:
                pipe.hdel("token_to_resource", token_secret)
                pipe.hdel("counter", token_secret)
            else:
                resource_ids.remove(resource_id)
                pipe.hset("token_to_resource", token_secret, json.dumps(list(resource_ids)))

                if raw_counter:
                    counter = json.loads(raw_counter)
                    del counter[resource_id]
                    pipe.hset("counter", token_secret, json.dumps(counter))

            pipe.execute()
