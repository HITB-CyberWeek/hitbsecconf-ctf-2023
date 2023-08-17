from flask import *
import datetime,os,random,string
import dataset
from threading import Lock
from functools import wraps
import re
import token_generator

app = Flask(__name__)
if os.path.isfile("secret_string.txt"):
    app.secret_key = open("secret_string.txt").read()
else:
    app.secret_key = ''.join(random.choice(string.ascii_lowercase) for i in range(16))
    open("secret_string.txt","w").write(app.secret_key)

DB = "data.db"
DB_lock = Lock()
def db_access(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        global DB_lock,DB
        DB_lock.acquire()
        db = dataset.connect(f'sqlite:///{DB}')
        args=tuple([db]+list(args))
        result = fn(*args, **kwargs)
        db.executable.close()
        DB_lock.release()
        return result
    return wrapper
def Init():
    if not os.path.isfile(DB):
        DB_lock.acquire()
        open(DB,"a").write("")
        db = dataset.connect(f'sqlite:///{DB}')
        db.query("CREATE TABLE users (id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,login TEXT, password TEXT, reg_date TEXT)")
        db.query("CREATE TABLE licences (id INTEGER NOT NULL PRIMARY KEY,user_id INTEGER, token TEXT NOT NULL, licence TEXT NOT NULL, create_date TEXT)")
        db.executable.close()
        DB_lock.release()
@db_access
def FindUsers(db,pattern):
    res = db.query("SELECT * FROM users where login like '%"+pattern+"%'")
    result=[]
    for r in res:
        result.append((r['login'],r['reg_date']))
    return result
@db_access
def GetUser(db,login):
    res = db['users'].find_one(login=login)
    if not res:
        return False
    return res
@db_access
def CreateUser(db,login,password):
    db['users'].insert(dict(login=login,password=password,reg_date=str(datetime.datetime.now())))

@db_access
def AddLicence(db,user,token,licence):
    user_exists = db['users'].find_one(login=user)
    if user_exists is None:
        return None
    print(user_exists)
    new_licence = {
        'user_id': user_exists['id'],
        'token': token,
        'licence': licence,
        'create_date': str(datetime.datetime.now())
    }
    db['licences'].insert(new_licence)
    return True
@db_access
def GetLicense(db,token):
    token_exists = db['licences'].find_one(token=token)
    if not token_exists :
        return None
    return token_exists['licence']

#--------------------------------------------------
@app.route("/")
def index():
    if 'user' in session:
        return render_template("all_companies.html",user=session['user'])
    else:
        return render_template("all_companies.html")

@app.route("/enter")
def enter():
    return render_template("reg.html")

@app.route("/make_license",methods=["POST"])
def makelic():
    if not "license_key" in request.values:
        return render_template("all_companies.html",message="No license to add",user=session['user'])
    if not 'user' in session:
        return render_template("all_companies.html",message="No logged in",user=session['user'])
    license = request.values['license_key']
    company = session['user']
    token = token_generator.GetTOK()

    if type(token) == type(b''):
        token=token.decode()
    res = AddLicence(company,token,license)
    if not res:
        return render_template("all_companies.html",message="No such user")
    return render_template("all_companies.html",message="Successfully added. Your token is "+ token,user=session['user'])

@app.route("/get_token",methods=["GET"])
def gettok():
    if not "token" in request.values:
        if 'user' in session:
            return render_template("all_companies.html",message="No token provided",user=session['user'])
        else:
            return render_template("all_companies.html",message="No token provided")
    token = request.values['token']
    lic = GetLicense(token)
    if not lic:
        if 'user' in session:
            return render_template("all_companies.html",message="No such token",user=session['user'])
        else:
            return render_template("all_companies.html",message="No such token")
    if 'user' in session:
        return render_template("all_companies.html",message="Your license is "+ lic,user=session['user'])
    else:
        return render_template("all_companies.html",message="Your license is " + lic)


@app.route("/register",methods=["POST"])
def register():
    if not "login" in request.values \
        or not 'password' in request.values:
        return render_template("reg.html",message="No fields")
    login = request.values['login']
    password = request.values['password']
    if len(login)<=4 or len(password) <=4:
        return render_template("reg.html",message="Too short login or password")
    db_user = GetUser(login)
    if not db_user:
        CreateUser(login,password)
        session['user'] = login
        return redirect("/")
    else:
        return render_template("reg.html",message="Already exists")

def check_alphanumeric(input_str):
    if re.match("^[a-zA-Z0-9]+$", input_str):
        return True
    else:
        return False

@app.route("/search",methods=["GET"])
def search():
    if not "pattern" in request.values:
        if 'user' in session:
            return render_template("all_companies.html",message="No pattern provided",user=session['user'])
        else:
            return render_template("all_companies.html",message="No pattern provided")
    if len(request.values['pattern']) < 2:
        if 'user' in session:
            return render_template("all_companies.html",message="Too short pattern",user=session['user'])
        else:
            return render_template("all_companies.html",message="Too short pattern")
    if not check_alphanumeric(request.values['pattern']):
        if 'user' in session:
            return render_template("all_companies.html",message="Not alphanumeric",user=session['user'])
        else:
            return render_template("all_companies.html",message="Not alphanumeric")

    pattern = request.values['pattern']
    found_users = FindUsers(pattern)
    if 'user' in session:
        return render_template("all_companies.html",results_search=found_users,user=session['user'])
    else:
        return render_template("all_companies.html",results_search=found_users)


@app.route("/login",methods=["POST"])
def login():
    if not "login" in request.values \
        or not 'password' in request.values:
        return render_template("reg.html",message="No fields")
    login = request.values['login']
    password = request.values['password']
    db_user = GetUser(login)
    if not db_user:
        return render_template("reg.html",message="No such user")
    if db_user['password'] != password:
        return render_template("reg.html",message="Invalid password")
    session['user'] = login
    return redirect("/")

@app.route("/logout")
def logout():
    del session['user']
    return redirect("/")
app.run(host="0.0.0.0",debug=True,threaded=True,port=5555)
