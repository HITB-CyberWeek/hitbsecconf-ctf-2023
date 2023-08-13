import random
import string

ALPHA = string.ascii_letters + string.digits


def gen_string(a=20, b=20):
    return ''.join(random.choice(ALPHA) for _ in range(random.randint(a, b)))


def gen_token_name():
    return gen_string(10, 20)


def gen_password():
    return gen_string()


def gen_resource_name():
    return 'Resource ' + gen_string()


def gen_resource_data():
    return gen_string(50, 100)
