import util
import redis


class SessionManager:
    def __init__(self, redis_conn: redis.Redis):
        self.redis_conn = redis_conn

    def create(self, username):
        salt = util.gen_str()
        secret = util.base_hash(username + salt)

        self.redis_conn.set(username, salt)

        return secret

    def delete(self, username):
        self.redis_conn.delete(username)

    def validate(self, username, secret):
        salt = self.redis_conn.get(username)
        if not salt:
            return False
        salt = salt.decode()

        return util.base_hash(username + salt) == secret
