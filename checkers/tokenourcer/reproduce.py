import random
import string

import requests


ALP = string.ascii_letters + string.digits


def gen_str(a=0, b=20):
    return ''.join(random.choice(ALP) for _ in range(a, b))


def main():
    username = 'user_' + gen_str()
    data = {
        'username': username,
        'password': gen_str()
    }
    url = 'http://localhost:8080/register'
    r = requests.post(url, json=data)
    print(r)
    print(r.cookies)

    url = 'http://localhost:8080/login'
    # data['username'] = '123'
    r = requests.post(url, json=data)
    print(r)
    print(r.cookies)

    cookies = r.cookies

    url = 'http://localhost:8080/issue_token'
    r = requests.post(url, cookies=cookies)
    print(r)
    print(r.json())
    token0 = r.json()['token']

    url = 'http://localhost:8080/issue_token'
    r = requests.post(url, cookies=cookies)
    print(r)
    print(r.json())
    token1 = r.json()['token']

    url = 'http://localhost:8080/create_resource'
    data = {
        'token': token0,
        'blob': 'FLAG_' + gen_str()
    }
    r = requests.post(url, json=data, cookies=cookies)
    print(r)
    print(r.json())
    resource_id = r.json()['resource_id']

    url = 'http://localhost:8080/get_resource?username={}&token={}&resource_id={}'.format(username, token0, resource_id)
    r = requests.get(url)
    print(r)
    print(r.json())

    url = 'http://localhost:8080/grant_access'
    data = {
        'token': token0,
        'resource_id': 'ne-res',
    }
    r = requests.post(url, json=data, cookies=cookies)
    print(r)
    print(r.json())

    url = 'http://localhost:8080/remove_resource'
    data = {
        'username': username,
        'token': token0,
        'resource_id': resource_id,
    }

    try:
        r = requests.post(url, json=data, cookies=cookies)
        print(r)
        print(r.json())
    except Exception:
        pass

    url = 'http://localhost:8080/list_resources'
    r = requests.get(url, cookies=cookies)
    print(r)
    print(r.json())


if __name__ == '__main__':
    main()
