import base64
import hashlib
import random
import string


ALP = string.ascii_letters + string.digits


def gen_str(a=0, b=20):
    return ''.join(random.choice(ALP) for _ in range(a, b))


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
