import requests,sys
import string
import random
def id_gen(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

sess = requests.Session()

if len(sys.argv) <= 2:
    quit()
ip = sys.argv[1]
PORT = 8081
proc = sys.argv[2]
url = f"http://{ip}:{PORT}/"

if proc == 'check':
    res = sess.get(url)

    login1=id_gen(10)
    password1=id_gen(10)
    res = sess.post(url+"register",
            data=dict(login=login1,password=password1))
    if not f"Logged in as {login1}" in res.text:
        print("Cannot register as login1")
        exit(102)
    sess.get(url+"/logout")
    res = sess.post(url+"login",
            data=dict(login=login1,password=password1))
    if not f"Logged in as {login1}" in res.text:
        print("Cannot login as login1")
        exit(102)
    mes=id_gen(100)
    sess.post(url+"addwall",
            data=dict(message=mes))
    res = sess.get(url)
    if not mes in res.text:
        print("Cannot leave message on wall")
        exit(102)
    login2=id_gen(10)
    password2=id_gen(10)
    sess2 = requests.Session()
    res = sess2.post(url+"register",
            data=dict(login=login2,password=password2))
    if not f"Logged in as {login2}" in res.text:
        print("Cannot register as login2")
        exit(102)
    mes = id_gen(50)
    res = sess2.post(url+"addprivate",
            data=dict(user=login1,message=mes))
    res = sess.get(url)
    if not mes in res.text:
        print("Cannot leave message on wall")
        exit(102)
    print("OK")
    exit(101)
