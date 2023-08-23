#!/usr/bin/env python3

import sys
import traceback
import requests
import random
import string
import http
import json
import ssl
import socket
import os
from urllib.parse import urljoin
from lxml import etree
from random import randint
from faker import Faker
requests.packages.urllib3.disable_warnings()
from checker_helper import *

VERIFY = False
TIMEOUT = 30
ADMIN_CERT = 'admin.crt'
ADMIN_KEY = 'admin.key'

fake = Faker()

def info():
    verdict(OK, "vulns: 1\npublic_flag_description: Flag ID is the ID of the contact containing the flag")


def get_random_string(min_len, max_len):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(random.randint(min_len, max_len)))

def get_url_path(path, use_client_cert):
    if not use_client_cert:
        return path

    if not os.getenv('DEV'):
        return f"/private{path}"

    return path

def register_user(host, user, password, use_client_cert=False):
    base_url = f"https://{host}/"

    session = requests.Session()

    trace(f"Trying to register using {user}:{password} (use_client_cert={use_client_cert})")

    if use_client_cert:
        cert=(ADMIN_CERT, ADMIN_KEY)
    else:
        cert=None

    if random.choice([0, 1]):
        url = urljoin(base_url, get_url_path('/', use_client_cert))
        trace(f"Going to '{url}' and waiting for a redirect to '/login'")
        try:
            r = session.get(url, timeout=TIMEOUT, verify=VERIFY, cert=cert)
        except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected, socket.error) as e:
            return (DOWN, "Connection error", "Connection error during requesting home page: %s" % e, None, None)
        except requests.exceptions.Timeout as e:
            return (DOWN, "Timeout", "Timeout during requesting home page: %s" % e, None, None)

        if r.status_code == 502 or r.status_code == 504:
            return (DOWN, "Connection error", "@andgein forced me to return DOWN for 502 Bad Gateway", None, None)

        if r.status_code != 200:
            return (MUMBLE, "Unexpected result", "Unexpected HTTP status code when requesting home page without session cookie: '%d'" % r.status_code, None, None)

        if r.request.url != urljoin(base_url, get_url_path('/login', use_client_cert)):
            return (MUMBLE, "Unexpected result", f"Unexpected login url '{r.request.url}' when requesting home page without session cookie. Expected url: '{urljoin(base_url, get_url_path('/login', use_client_cert))}'", None, None)

        headers = {'Referer': urljoin(base_url, '/login')}
        url = urljoin(base_url, get_url_path('/register', use_client_cert))
        trace(f"Going to '{url}' from login page")
        try:
            r = session.get(url, headers=headers, timeout=TIMEOUT, verify=VERIFY, cert=cert)
        except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected, socket.error) as e:
            return (DOWN, "Connection error", "Connection error during requesting registration page: %s" % e, None, None)
        except requests.exceptions.Timeout as e:
            return (DOWN, "Timeout", "Timeout during requesting registration page: %s" % e, None, None)
    
        if r.status_code == 502 or r.status_code == 504:
            return (DOWN, "Connection error", "@andgein forced me to return DOWN for 502 Bad Gateway", None, None)
    
        if r.status_code != 200:
            return (MUMBLE, "Unexpected result", "Unexpected HTTP status code when requesting registration page: '%d'" % r.status_code, None, None)

        headers = {'Referer': urljoin(base_url, '/register')}
    else:
        headers = {}

    url = urljoin(base_url, get_url_path('/register', use_client_cert))
    trace(f"Sending the registration data to '{url}'")
    data = {"username": user, "password": password}
    try:
        r = session.post(url, data=data, headers=headers, timeout=TIMEOUT, verify=VERIFY, cert=cert)
    except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected, socket.error) as e:
        return (DOWN, "Connection error", "Connection error during registration: %s" % e, None, None)
    except requests.exceptions.Timeout as e:
        return (DOWN, "Timeout", "Timeout during registration: %s" % e, None, None)

    if r.status_code == 502 or r.status_code == 504:
        return (DOWN, "Connection error", "@andgein forced me to return DOWN for 502 Bad Gateway", None, None)

    if r.status_code != 200:
        return (MUMBLE, "Can't register", "Unexpected registration result: '%d'" % r.status_code, None, None)

    try:
        parser = etree.HTMLParser()
        parser.feed(r.text)
        doc = parser.close()
    except Exception as e:
        return (MUMBLE, "Unexpected registration result", "Can't parse result html: '%s'" % e, None, None)

    user_element = doc.xpath("//span[@id='username']")
    if len(user_element) != 1:
        return (MUMBLE, "Unexpected registration result", "Can't find username HTML element in '%s'" % r.text, None, None)

    actual_user = user_element[0].text.removesuffix(' | ').strip()
    if actual_user != user:
        return (MUMBLE, "Unexpected registration result", "Wrong username: '%s'" % actual_user, None, None)

    trace("Successfully registered")
    return (OK, "", "", session, r.text)


def login_user(host, user, password, use_client_cert=False):
    base_url = f"https://{host}/"

    if use_client_cert:
        cert=(ADMIN_CERT, ADMIN_KEY)
    else:
        cert=None

    session = requests.Session()

    if random.choice([0, 1]):
        url = urljoin(base_url, get_url_path('/', use_client_cert))
        trace("Going to '%s' and waiting for a redirect to '/login'" % url)
        try:
            r = session.get(url, timeout=TIMEOUT, verify=VERIFY, cert=cert)
        except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected, socket.error) as e:
            return (DOWN, "Connection error", "Connection error during requesting home page: %s" % e, None, None)
        except requests.exceptions.Timeout as e:
            return (DOWN, "Timeout", "Timeout during requesting home page: %s" % e, None, None)

        if r.status_code == 502 or r.status_code == 504:
            return (DOWN, "Connection error", "@andgein forced me to return DOWN for 502 Bad Gateway", None, None)

        if r.status_code != 200:
            return (MUMBLE, "Unexpected result", "Unexpected HTTP status code when requesting home page without session cookie: '%d'" % r.status_code, None, None)

        if r.request.url != urljoin(base_url, get_url_path('/login', use_client_cert)):
            return (MUMBLE, "Unexpected result", "Unexpected login url when requesting home page without session cookie: '%s'" % r.request.url, None, None)

        headers = {'Referer': urljoin(base_url, '/login')}
    else:
        headers = {}

    trace(f"Trying to login using {user}:{password} (use_client_cert={use_client_cert})")
    data = {"username": user, "password": password}

    url = urljoin(base_url, get_url_path('/login', use_client_cert))
    try:
        r = session.post(url, data=data, headers=headers, timeout=TIMEOUT, verify=VERIFY, cert=cert)
    except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected, socket.error) as e:
        return (DOWN, "Connection error", "Connection error during login: %s" % e, None, None)
    except requests.exceptions.Timeout as e:
        return (DOWN, "Timeout", "Timeout during login: %s" % e, None, None)

    if r.status_code == 502 or r.status_code == 504:
        return (DOWN, "Connection error", "@andgein forced me to return DOWN for 502 Bad Gateway", None, None)

    if r.status_code != 200:
        return (MUMBLE, "Can't login", "Unexpected login result: '%d'" % r.status_code, None, None)

    try:
        parser = etree.HTMLParser()
        parser.feed(r.text)
        doc = parser.close()
    except Exception as e:
        return (MUMBLE, "Unexpected login result", "Can't parse result html: '%s'" % e, None, None)

    user_element = doc.xpath("//span[@id='username']")
    if len(user_element) != 1:
        return (MUMBLE, "Unexpected login result", "Can't find username HTML element in '%s'" % r.text, None, None)

    actual_user = user_element[0].text.removesuffix(' | ').strip()
    if actual_user != user:
        return (MUMBLE, "Unexpected login result", "Wrong username: '%s'" % actual_user, None, None)

    trace("Successfully logged in")
    return (OK, "", "", session, r.text)


def get_contact_id_by_name(home_page_html, name):
    try:
        parser = etree.HTMLParser()
        parser.feed(home_page_html)
        doc = parser.close()
    except Exception as e:
        return (MUMBLE, "Unexpected result", "Can't parse home page html: '%s'" % e, None)

    row_element = doc.xpath("//tbody/tr[td/a[contains(text(), '%s')]]" % name)

    if len(row_element) == 0:
        return (CORRUPT, "Can't find contact", "Can't find contact", None)

    if len(row_element) != 1:
        return (MUMBLE, "Unexpected result", "Can't find contact '%s' in '%s'" % (name, home_page_html), None)

    contact_id = row_element[0].xpath("./td[contains(@class, 'js-name')]/a/@href")[0].rsplit('/', 1)[-1]
    return (OK, "", "", contact_id)


def generate_random_contact(comment = None):
    data = {}

    data["firstName"] = fake.first_name()
    data["lastName"] = fake.last_name()

    if random.choice([0, 1]):
        data["title"] = fake.job()

    if random.choice([0, 1]):
        data["organization"] = fake.company()

    if random.choice([0, 1]):
        data["email"] = fake.company_email()

    if random.choice([0, 1]):
        data["phone"] = fake.phone_number()

    if comment:
        data["comment"] = comment
    else:
        if random.choice([0, 1]):
            data["comment"] = fake.paragraph(nb_sentences=random.choice([1,2]))

    return data


def create_contact(host, session, comment, use_client_cert=False):
    base_url = f"https://{host}/"

    if use_client_cert:
        cert=(ADMIN_CERT, ADMIN_KEY)
    else:
        cert=None

    data = generate_random_contact(comment)

    if random.choice([0, 1]):
        headers = {'Referer': base_url}
        url = urljoin(base_url, get_url_path('/add', use_client_cert))
        trace(f"Going to the '{url}' page from home page")
        try:
            r = session.get(url, headers=headers, timeout=TIMEOUT, verify=VERIFY, cert=cert)
        except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected, socket.error) as e:
            return (DOWN, "Connection error", "Connection error during requesting '/add' page: %s" % e, None, None)
        except requests.exceptions.Timeout as e:
            return (DOWN, "Timeout", "Timeout during requesting '/add' page: %s" % e, None, None)
    
        if r.status_code == 502 or r.status_code == 504:
            return (DOWN, "Connection error", "@andgein forced me to return DOWN for 502 Bad Gateway", None, None)
    
        if r.status_code != 200:
            return (MUMBLE, "Unexpected result", "Unexpected HTTP status code when requesting '/add' page: '%d'" % r.status_code, None, None)

        headers = {'Referer': urljoin(base_url, '/add')}
    else:
        headers = {}

    try:
        url = urljoin(base_url, get_url_path('/add', use_client_cert))
        r = session.post(url, data=data, headers=headers, timeout=TIMEOUT, verify=VERIFY, cert=cert)
    except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected, socket.error) as e:
        return (DOWN, "Connection error", "Connection error during creating contact: %s" % e, None, None)
    except requests.exceptions.Timeout as e:
        return (DOWN, "Timeout", "Timeout during creating contact: %s" % e, None, None)

    if r.status_code == 502 or r.status_code == 504:
        return (DOWN, "Connection error", "@andgein forced me to return DOWN for 502 Bad Gateway", None, None)

    if r.status_code != 200:
        return (MUMBLE, "Can't create contact", "Unexpected status code when creating a contact: '%d'" % r.status_code, None, None)

    name = "%s %s" % (data["firstName"], data["lastName"])
    (status, out, err, contact_id) = get_contact_id_by_name(r.text, name)
    if status != OK:
        if status == CORRUPT:
            status = MUMBLE
        return (status, out, err, None, None)

    trace("Contact '%s' successfully created" % name)

    return (OK, "", "", contact_id, name)


def get_contact_comment(host, session, id, use_client_cert=False):
    base_url = f"https://{host}/"

    if use_client_cert:
        cert=(ADMIN_CERT, ADMIN_KEY)
    else:
        cert=None

    if random.choice([0, 1]):
        headers = {'Referer': base_url}
    else:
        headers = {}

    url = urljoin(base_url, get_url_path(f"/edit/{id}", use_client_cert))
    try:
        r = session.get(url, headers=headers, timeout=TIMEOUT, verify=VERIFY, cert=cert)
    except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected, socket.error) as e:
        return (DOWN, "Connection error", "Connection error during reading a contact: %s" % e, None)
    except requests.exceptions.Timeout as e:
        return (DOWN, "Timeout", "Timeout during reading a contact: %s" % e, None)

    if r.status_code == 502 or r.status_code == 504:
        return (DOWN, "Connection error", "@andgein forced me to return DOWN for 502 Bad Gateway", None)

    if r.status_code != 200:
        return (MUMBLE, "Can't get contact", "Unexpected status code when reading a contact: '%d'" % r.status_code, None)

    try:
        parser = etree.HTMLParser()
        parser.feed(r.text)
        doc = parser.close()
    except Exception as e:
        return (MUMBLE, "Unexpected result", "Can't parse contact html: '%s'" % e, None)

    contact_comment = doc.xpath("//textarea[@name='comment']/text()")

    if len(contact_comment) != 1:
        return (MUMBLE, "Unexpected result", "Can't find comment in '%s'" % r.text, None)

    trace("Successfully got contact comment: '%s'" % contact_comment[0].strip())
    return (OK, "", "", contact_comment[0].strip())

def switch_dark_mode(host, dark_mode):
    base_url = f"https://{host}/"

    session = requests.Session()
    if not dark_mode is None:
        if dark_mode:
            trace("Set settings cookie to 'darkMode:1'")
            session.cookies.set("settings", "darkMode:1")
        else:
            trace("Set settings cookie to 'darkMode:0'")
            session.cookies.set("settings", "darkMode:0")

    url = urljoin(base_url, '/')
    trace("Going to '%s' and waiting for a redirect to '/login'" % url)
    try:
        r = session.get(url, timeout=TIMEOUT, verify=VERIFY)
    except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected, socket.error) as e:
        return (DOWN, "Connection error", "Connection error during requesting home page: %s" % e, None)
    except requests.exceptions.Timeout as e:
        return (DOWN, "Timeout", "Timeout during requesting home page: %s" % e, None)

    if r.status_code == 502 or r.status_code == 504:
        return (DOWN, "Connection error", "@andgein forced me to return DOWN for 502 Bad Gateway", None)

    if r.status_code != 200:
        return (MUMBLE, "Unexpected result", "Unexpected HTTP status code when requesting home page without session cookie: '%d'" % r.status_code, None)

    if r.request.url != urljoin(base_url, '/login'):
        return (MUMBLE, "Unexpected result", "Unexpected login url when requesting home page without session cookie: '%s'" % r.request.url, None)

    return (OK, "", "", r.text)

def get_theme(html):
    try:
        parser = etree.HTMLParser()
        parser.feed(html)
        doc = parser.close()
    except Exception as e:
        return (MUMBLE, "Unexpected result", "Can't parse html: '%s'" % e, None)

    theme = doc.xpath("/*/@data-bs-theme")

    if len(theme) != 1:
        return (MUMBLE, "Unexpected result", "Can't find 'data-bs-theme' attribute in '%s'" % r.text, None)

    trace("Successfully got 'data-bs-theme' attribute: '%s'" % theme[0])
    return (OK, "", "", theme[0])

    return (OK, "", "", "")

def put(args):
    if len(args) != 4:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for put()")
    host, flag_id, flag, vuln = args
    trace("put(%s, %s, %s, %s)" % (host, flag_id, flag, vuln))

    user = get_random_string(5, 15)
    password = get_random_string(7, 20)

    if random.choice([0, 1]):
        use_client_cert = True
    else:
        use_client_cert = False

    (status, out, err, session, home_page_html) = register_user(host, user, password, use_client_cert)
    if status != OK:
        verdict(status, out, err)

    (status, out, err, contact_id, name) = create_contact(host, session, flag, use_client_cert)
    if status != OK:
        verdict(status, out, err)

    flag_id = json.dumps({"public_flag_id": contact_id, "name": name, "user": user, "password": password})
    verdict(OK, flag_id)


def get(args):
    if len(args) != 4:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for get()")
    host, flag_id, flag_data, vuln = args
    trace("get(%s, %s, %s, %s)" % (host, flag_id, flag_data, vuln))

    info = json.loads(flag_id)
    user = info['user']
    password = info['password']
    contact_id = info['public_flag_id']
    name = info['name']

    if random.choice([0, 1]):
        user = get_random_string(5, 15)
        password = get_random_string(7, 20)
        (status, out, err, session, home_page_html) = register_user(host, user, password, use_client_cert=True)

        if status != OK:
            verdict(status, out, err)

        (status, out, err, contact_id) = get_contact_id_by_name(home_page_html, name)
        if status != OK:
            verdict(status, out, err)

        (status, out, err, contact_comment) = get_contact_comment(host, session, contact_id, use_client_cert=True)
        if status != OK:
            verdict(status, out, err)
    else:
        (status, out, err, session, home_page_html) = login_user(host, user, password)
        if status != OK:
            verdict(status, out, err)

        (status, out, err, contact_id) = get_contact_id_by_name(home_page_html, name)
        if status != OK:
            verdict(status, out, err)

        (status, out, err, contact_comment) = get_contact_comment(host, session, contact_id)
        if status != OK:
            verdict(status, out, err)

    if contact_comment != flag_data:
        verdict(CORRUPT, "Can't find flag in contact", "Can't find flag in contact comment, actual flag: '%s'" % contact_comment)

    verdict(OK)


def check(args):
    if len(args) != 1:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for check()")
    host = args[0]
    trace("check(%s)" % host)

    choice = random.choice([0, 1, 2])
    if choice == 0:
        dark_mode = None
        expected = 'light'
    elif choice == 1:
        dark_mode = True
        expected = 'dark'
    else:
        dark_mode = False
        expected = 'light'

    (status, out, err, html) = switch_dark_mode(host, dark_mode)
    if status != OK:
        verdict(status, out, err)

    (status, out, err, theme) = get_theme(html)
    if status != OK:
        verdict(status, out, err)

    if theme != expected:
        verdict(MUMBLE, 'Unexpected result', f"Unexpected theme '{theme}', expected '{expected}'")

    verdict(OK)


def main(args):
    if len(args) == 0:
        verdict(CHECKER_ERROR, "Checker error", "No args")
    try:
        if args[0] == "info":
            info()
        elif args[0] == "check":
            check(args[1:])
        elif args[0] == "put":
            put(args[1:])
        elif args[0] == "get":
            get(args[1:])
        else:
            verdict(CHECKER_ERROR, "Checker error", "Wrong action: " + args[0])
    except Exception as e:
        verdict(CHECKER_ERROR, "Checker error", "Exception: %s" % traceback.format_exc())

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
        verdict(CHECKER_ERROR, "Checker error", "No verdict")
    except Exception as e:
        verdict(CHECKER_ERROR, "Checker error", "Exception: %s" % e)
