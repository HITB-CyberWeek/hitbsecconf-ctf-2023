import json
import uuid


class StorageApi:
    def __init__(self, redis_client):
        self.redis_client = redis_client

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
        raw_tokens = self.redis_client.hget("resource_to_tokens", resource_id)
        if not raw_tokens:
            tokens = [token_secret]
        else:
            tokens = json.loads(raw_tokens) + [token_secret]
        self.redis_client.hset("resource_to_tokens", resource_id, json.dumps(tokens))

    def get_tokens_by_resource_id(self, resource_id):
        raw_tokens = self.redis_client.hget("resource_to_tokens", resource_id)
        if raw_tokens:
            return json.loads(raw_tokens)
        return []

    def remove_resource_to_token(self, resource_id, token_secret):
        tokens = self.get_tokens_by_resource_id(resource_id)
        if len(tokens) == 1:
            self.redis_client.hdel("resource_to_tokens", resource_id)
        else:
            tokens.remove(token_secret)
            self.redis_client.hset("resource_to_tokens", resource_id, json.dumps(tokens))

    def add_token_to_resource(self, token_secret, resource_id):
        raw_resources = self.redis_client.hget("token_to_resource", token_secret)
        if raw_resources:
            resources = set(json.loads(raw_resources)) | {resource_id}
        else:
            resources = {resource_id}
        self.redis_client.hset("token_to_resource", token_secret, json.dumps(list(resources)))

    def get_resource_ids_by_token(self, token_secret):
        raw_resource_ids = self.redis_client.hget("token_to_resource", token_secret)
        if raw_resource_ids:
            return set(json.loads(raw_resource_ids))
        return set()

    def create_counter(self, token_secret, resource_id):
        self.redis_client.hset("counter", token_secret, json.dumps({resource_id: 0}))

    def inc_counter(self, token_secret, resource_id):
        raw_counter = self.redis_client.hget("counter", token_secret)
        if raw_counter:
            counter = json.loads(raw_counter)
            if resource_id not in counter:
                counter[resource_id] = 0
            counter[resource_id] += 1
        else:
            raise KeyError(token_secret)  # TODO: fix it!
            counter = {resource_id: 1}
        self.redis_client.hset("counter", token_secret, json.dumps(counter))

    def del_counter(self, token_secret, resource_id):
        raw_counter = self.redis_client.hget("counter", token_secret)
        if raw_counter:
            counter = json.loads(raw_counter)
            del counter[resource_id]
            self.redis_client.hset("counter", token_secret, json.dumps(counter))

    def remove_token_to_resource(self, token_secret, resource_id):
        resource_ids = self.get_resource_ids_by_token(token_secret)
        if len(resource_ids) == 1:
            self.redis_client.hdel("token_to_resource", token_secret)
            self.redis_client.hdel("counter", token_secret)
        else:
            resource_ids.remove(resource_id)
            self.redis_client.hset("token_to_resource", token_secret, json.dumps(list(resource_ids)))
            self.del_counter(token_secret, resource_id)
