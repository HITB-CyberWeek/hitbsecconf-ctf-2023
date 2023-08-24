#!/usr/bin/env python3
import requests,sys,string,random,re,logging,json


logging.basicConfig(format='%(asctime)-15s [%(levelname)s] %(message)s',
                    level=logging.DEBUG)

def id_gen(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

sess = requests.Session()

if len(sys.argv) <= 1:
    print("No command provided")
    exit(110)
proc = sys.argv[1]

def get_url(ip):
    if ip == "localhost":
        port = 8080
        return f"http://{ip}:{port}/"
    return f"https://{ip}/"

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

    return myhash == h

try:
    if proc == 'check':
        ip = sys.argv[2]
        url = get_url(ip)
        res = sess.get(url)
        if res.status_code != 200:
            logging.info("Cannot connect to service")
            exit(104)

        logging.info("Initial page received")

        login1=id_gen(10)
        password1=id_gen(10)
        testlic=id_gen(10)


        res = sess.get(url+"enter")
        logging.info("Going to /enter")
        if not "Register new company" in res.text:
            logging.error("Can not find 'Register new company' at the /enter page")
            print("Can not register a new company")
            exit(102)


        res = sess.post(url+"register",data=dict(login=login1,password=password1))
        logging.info("Registering new company " + login1 + " "+ password1)
        if not "Logged in as "+login1 in res.text:
            print("Can not register a new company")
            exit(102)
        logging.info("Successfully registered")
        sess.get(url+"logout")
        logging.info("Logging out")
        res = sess.get(url+"search?pattern="+login1[:2])
        logging.info("Searching company " + login1[:2])
        if not login1 in res.text:
            print("Can not find freshly registered company")
            exit(102)
        logging.info("Company found")

        res = sess.post(url+"register",data=dict(login=login1,password=password1))
        logging.info("Trying duplicate register")
        if not "Already exists" in res.text:
            print("Can register twice with the same login")
            exit(102)

        res = sess.post(url+"login",data=dict(login=login1,password=password1))
        logging.info("Trying to log in "+ login1 + " "+ password1)
        if not "Logged in as "+login1 in res.text:
            print("Can not login")
            exit(102)
        logging.info("Logged in")

        res = sess.post(url+"make_license",data=dict(license_key=testlic))
        logging.info("Making token for "+testlic)
        res1 = re.findall(r'Successfully added. Your token is ([0-9A-Za-z]+)',res.text)
        if len(res1) != 1:
            print("Cannot find result token")
            exit(102)
        logging.info("Token received: "+ res1[0])

        if not VerifySign(res1[0]):
            print("Received token is incorrect")
            exit(102)
        logging.info("Token sign has been successfully verified")

        res = sess.get(url+"get_token?token="+res1[0])
        logging.info("Getting the license for the token "+res1[0])
        if not testlic in res.text:
            print("The license retrieved by the token is incorrect")
            exit(102)
        logging.info("License has been received")
        exit(101)
    elif proc == 'put':
        ip = sys.argv[2]
        url = get_url(ip)
        login1 = sys.argv[3]
        password1=id_gen(10)
        flag = sys.argv[4]
        logging.info("Registering company " + login1+" "+password1)
        res = sess.post(url+"register",data=dict(login=login1,password=password1))
        if not "Logged in as "+login1 in res.text:
            print("Can not register company")
            exit(102)
        logging.info("Registered")
        res = sess.post(url+"make_license",data=dict(license_key=flag))
        logging.info("Adding license "+ flag)
        res1 = re.findall(r'Successfully added. Your token is ([0-9A-Za-z]+)',res.text)
        if len(res1) != 1:
            print("Can not find token in the response")
            exit(102)
        logging.info("Successfuly added flag. Token is "+res1[0])
        if not VerifySign(res1[0]):
            print("Token is incorrect")
            exit(102)
        logging.info("Verified sign for token "+ res1[0])
        print(json.dumps({"public_flag_id": login1, "login": login1,"token":res1[0]}))
        # print(login1+","+res1[0])
        exit(101)
    elif proc == 'get':
        ip = sys.argv[2]
        url = get_url(ip)
        jsn = json.loads(sys.argv[3])#  list(sys.argv[3].split(","))
        login1,token = jsn['login'],jsn['token']
        flag = sys.argv[4]

        res = sess.get(url+"get_token?token="+token)
        logging.info("Getting license for token "+token)
        if not flag in res.text:
            logging.info("Can not find flag in "+res.text)
            print("Can not receive correct license by the token")
            exit(102)
        logging.info("Found flag in the result")
        exit(101)
    elif proc == "info":
        print("vulns: 1\npublic_flag_description: Flag ID is the name of the company, flag is the license")
        exit(101)
    else:
        print("No command provided")
        exit(110)
except requests.exceptions.ConnectionError as e:
    logging.error(f"Can not connect to the server: {e}", exc_info=e)
    print("Can not connect to the server")
    exit(104)
except ValueError as e:
    logging.error(f"ValueError received: {e}", exc_info=e)
    print("Token is incorrect")
    exit(102)
