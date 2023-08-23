#!/usr/bin/env python3

import json
import logging
import random
import string
import html
import jwt
import re
import urllib.parse
import checklib.http
import checklib.random
from checklib import StatusCode


def get_random_domain():
    word = checklib.random.english_word().lower()
    while len(word) < 2:
        word = checklib.random.english_word().lower()
    return word


class NoteChecker(checklib.http.HttpChecker):
    # port = 443
    # proto = 'https'
    port = 80
    proto = 'http'

    def info(self):
        print("vulns: 1")
        print("public_flag_description: Flag ID is the user's ID, flag is the note's description")

    def check(self, address):

        # check user creating
        user = self.create_user()
        self.logout()

        # check note creating 
        self.login(user)
        description = ""
        while len(description) < 15:
            description += f"{checklib.random.english_word()} "
        self.create_notes(description)
        self.logout()

        self.check_language(user)

        self.get_user_id(user)

        self.exit(checklib.StatusCode.OK)

    def put(self, address, flag_id, flag, vuln):
        user = self.create_user()
        self.create_notes(flag)
        if random.random() < .5:
            self.add_language(user)
        self.logout()

        public_flag_id = self.get_user_id(user)

        print(json.dumps({
            "public_flag_id": public_flag_id,
            "user": user
        }))

        self.exit(checklib.StatusCode.OK)

    def get(self, address, flag_id, flag, vuln):
        info = json.loads(flag_id)
        user = info["user"]
        self.login(user)
        response = self.try_http_get("/notes")
        self.check_page_content(response, [flag], "Could not find the flag in notes for the user " + user["email"])
        self.logout()

    def check_language(self, user):
        cookies = self.get_cookies()
        cookies['language'] = "ru"
        ru_response = self.try_http_post("/", cookies=cookies)

        cookies['language'] = "en"
        en_response = self.try_http_post("/", cookies=cookies)

        self.check_page_content(ru_response, ['Регистрация'], "The interface language has not changed to RU")
        self.check_page_content(en_response, ['Sign Up'], "The interface language has not changed to EN")

        self.add_language(user)

    def add_language(self, user):
        self.login(user)
        language_title = ''
        while len(language_title) < 5:
            language_title += checklib.random.english_word()
        data = {
            'title': language_title,
        }
        inputs_name = [
            "HOME", "SIGN_IN", "SIGN_UP", "EXIT", "WELCOME", "EMAIL", "PASSWORD", "NOTE", "NOTES", "NOTES_ADD", "TITLE",
            "NOTES_NOT_FOUND", "LANGUAGE_ADD", "LANGUAGE_ADDED", "TRANSLATION_FOR", "SHARED_LINK"
        ]
        for input_name in inputs_name:
            data[input_name] = checklib.random.english_word()
        response = self.try_http_post("/language/add", data=data)
        self.check_page_content(response, ['id="shared_link"'], "Invalid format of the response at POST /language/add")
        self.logout()

        self.create_user()
        links = re.findall(r'(http:.*)', response.text)
        set_language_link = html.unescape(links[0])
        parse_qs = urllib.parse.parse_qs(urllib.parse.urlparse(set_language_link).query)
        r = self.try_http_get(set_language_link)

        self.mumble_if_false(
            parse_qs.get("language")[0] == urllib.parse.unquote(self.get_cookies()['language']) and data['LANGUAGE_ADD'] in r.text,
            f"The interface language has not changed at GET {set_language_link}"
        )
        self.logout()

    def login(self, user):
        response = self.try_http_post(
            "/signin",
            data={"email": user['email'], "password": user['password']}
        )
        self.check_page_content(
            response,
            ['href="/notes"', user['email']],
            "Invalid format of the response at POST /signin"
        )

    def logout(self):
        self.try_http_post("/exit")
        self.mumble_if_false("jwt" not in self.get_cookies(), "Invalid format of the response at /exit")

    def create_user(self) -> dict:
        username = f"{checklib.random.firstname().lower()}_{checklib.random.firstname().lower()}"
        email = f"{username}@{get_random_domain()}.{get_random_domain()}"
        password = checklib.random.string(string.ascii_letters + string.digits, random.randint(8, 12))
        logging.info(f"Creating user {email} with password {password}")
        response = self.try_http_post(
            "/signup",
            data={"email": email, "password": password, "confirm_password": password}
        )

        self.check_page_content(
            response,
            ['href="/notes"', 'href="/notes/add/"'],
            "Invalid format of the response at POST /signup"
        )

        logging.info(f"Created user with email '{email}'")
        return {
            "email": email,
            "password": password
        }

    def create_notes(self, flag: str):
        title = ""
        while len(title) < 7:
            title += f"{checklib.random.english_word()} "
        response = self.try_http_post(
            "/notes/add/",
            data={
                "title": title,
                "description": flag
            }
        )
        logging.info(f"Created note with title '{title}'")
        self.check_page_content(
            response,
            [title, flag],
            "Invalid format of the response at POST /notes/add/"
        )

    def get_user_id(self, user):
        try:
            self.login(user)
            self.mumble_if_false('jwt' in self.get_cookies(), "Not found jwt in cookies")

            jwt_token = self.get_cookies().get('jwt')

            jwt_data = jwt.decode(jwt_token, options={"verify_signature": False})
            user_id = jwt_data.get('user_id', 0)
            self.mumble_if_false(
                user_id != 0, "User id not found in the JWT "
            )
            self.logout()
            return user_id
        except jwt.exceptions.DecodeError:
            self.exit(StatusCode.MUMBLE, "JWT decode error")


if __name__ == "__main__":
    NoteChecker().run()
