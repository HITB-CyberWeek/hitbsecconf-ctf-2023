import requests,sys,string,random,re
def id_gen(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

sess = requests.Session()

if len(sys.argv) <= 2:
    print("No command provided")
    exit(105)
ip = sys.argv[1]
PORT =  8080
proc = sys.argv[2]
url = f"http://{ip}:{PORT}/"

headers = requests.utils.default_headers()
headers.update(
    {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:106.0) Gecko/20100101 Firefox/106.0',
    }
)


def VerifySign(token):
    h = int(token[-8:],16)
    TOK1 = token[:-8]
    tmp1=""
    for c in [126, 93, 89, 110, 1, 94, 81, 15, 121, 80, 75, 1, 113, 95, 80, 14]:
        tmp1 += chr(c ^ 137)
    secret = tmp1

    tmp = secret + TOK1
    mybuff = tmp.encode()
    myhash = 0xABA21342  # начальное значение регистра
    for byte in mybuff:
        myhash ^= byte
        myhash = ((myhash >> 1) | (myhash << 31)) & 0xFFFFFFFF

    if myhash != h:
        return False
    return True


if proc == 'check':
    res = sess.get(url)
    login1=id_gen(10)
    password1=id_gen(10)
    testlic=id_gen(10)

    res = sess.get(url+"enter")
    if not "Register new company" in res.text:
        print("Cannot register 1")
        exit(102)

    res = sess.post(url+"register",data=dict(login=login1,password=password1))
    if not "Logged in as "+login1 in res.text:
        print("Cannot register 2")
        exit(102)
    sess.get(url+"/logout")
    res = sess.get(url+"search?pattern="+login1[:3])
    if not login1 in res.text:
        print("Cannot find registered company")
        exit(102)

    res = sess.post(url+"register",data=dict(login=login1,password=password1))
    if not "Already exists" in res.text:
        print("Can register twise")
        exit(102)

    res = sess.post(url+"login",data=dict(login=login1,password=password1))
    if not "Logged in as "+login1 in res.text:
        print("Cannot login")
        exit(102)

    res = sess.post(url+"make_license",data=dict(license_key=testlic))
    res1 = re.findall(r'Successfully added. Your token is ([0-9A-Za-z]+)',res.text)
    if len(res1) != 1:
        print("Cannot find result token")
        exit(102)

    if not VerifySign(res1[0]):
        print("Not a correct token")
        exit(102)

    res = sess.get(url+"get_token?token="+res1[0])
    if not testlic in res.text:
        print("Not a correct license by token")
        exit(102)
    exit(101)
elif proc == 'put':
    login1 = sys.argv[3]
    password1=id_gen(10)
    flag = sys.argv[4]
    res = sess.post(url+"register",data=dict(login=login1,password=password1))
    if not "Logged in as "+login1 in res.text:
        print("Cannot register 2")
        exit(102)
    res = sess.post(url+"make_license",data=dict(license_key=flag))
    res1 = re.findall(r'Successfully added. Your token is ([0-9A-Za-z]+)',res.text)
    if len(res1) != 1:
        print("Cannot find result token")
        exit(102)
    if not VerifySign(res1[0]):
        print("Not a correct token")
        exit(102)
    print(login1+","+res1[0])
    exit(101)
elif proc == 'get':
    login1,token = list(sys.argv[3].split(","))
    flag = sys.argv[4]

    res = sess.get(url+"get_token?token="+token)
    if not flag  in res.text:
        print("Not a correct license by token")
        exit(102)
    exit(101)
elif proc == "info":
    print("vulns: 1\npublic_flag_description: Flag ID is name of company\n")
    exit(101)
else:
    print("No command provided")
    exit(105)
