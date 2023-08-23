import base64
import hashlib
import secrets
import string


ALP = string.ascii_letters + string.digits


def gen_str(length):
    return ''.join(secrets.choice(ALP) for _ in range(length))


def gen_token_secret():
    return 'TOKEN_' + gen_str(32)


def get_hex_hash(data):
    hasher = hashlib.sha1()
    if isinstance(data, str):
        data = data.encode()
    hasher.update(data)
    return hasher.hexdigest()


def base_hash(data):
    hasher = hashlib.sha1()
    hasher.update(data.encode())
    return base64.b64encode(hasher.digest()).decode()
