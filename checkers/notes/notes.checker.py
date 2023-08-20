#!/usr/bin/env python3

import json
import logging
import random
import string
import jwt

import checklib.http
import checklib.random


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

        self.login(user)
        self.get_user_id()
        self.logout()

        self.exit(checklib.StatusCode.OK)

    def put(self, address, flag_id, flag, vuln):

        user = self.create_user()
        self.logout()
        self.login(user)
        self.create_notes(flag)
        public_flag_id = self.get_user_id()
        self.logout()

        print(json.dumps({
            "public_flag_id": public_flag_id,
            "user": user
        }))

        self.exit(checklib.StatusCode.OK)

    def get(self, address, flag_id, flag, vuln):
        info = json.loads(flag_id)
        user = info["user"]
        r = self.try_http_post(
            "/signin",
            data={"email": user['email'], "password": user['password']}
        )
        check_donate_2 = self.try_http_get("/notes")
        self.corrupt_if_false(
            flag in check_donate_2.text,
            "Could not find the flag in notes for the user " + user["email"]
        )
        self.logout()

    def login(self, user):
        r = self.try_http_post(
            "/signin",
            data={"email": user['email'], "password": user['password']}
        )
        self.mumble_if_false(
            'href="/notes"' in r.text, "Invalid format of the response at POST /signin"
        )

    def logout(self):
        r = self.try_http_post("/exit")
        self.mumble_if_false("Welcome!" in r.text, "Invalid format of the response at /exit")

    def create_user(self) -> dict:
        username = f"{checklib.random.firstname().lower()}_{checklib.random.firstname().lower()}"
        email = f"{username}@{get_random_domain()}.{get_random_domain()}"
        password = checklib.random.string(string.ascii_letters + string.digits, random.randint(8, 12))
        logging.info(f"Creating user {username} with password {password}")
        r = self.try_http_post(
            "/signup",
            data={"email": email, "password": password, "confirm_password": password}
        )

        self.mumble_if_false(
            'href="/notes"' in r.text and 'href="/notes/add/"' in r.text, "Invalid format of the response at POST /signup"
        )
        logging.info(f"Created user with username {username}")
        return {
            "username": username,
            "email": email,
            "password": password
        }

    def create_notes(self, flag: str):
        title = ""
        while len(title) < 7:
            title += f"{checklib.random.english_word()} "
        create_note = self.try_http_post(
            "/notes/add/",
            data={
                "title": title,
                "description": flag
            }
        )

        self.mumble_if_false(title in create_note.text and flag in create_note.text,
                             "Invalid format of the response at POST /notes/add/")

    def get_user_id(self):
        self.mumble_if_false('jwt' in self.get_cookies(), "Not found jwt in cookies")
        jwt_token = self.get_cookies().get('jwt')
        jwt_data = jwt.decode(jwt_token, options={"verify_signature": False})
        user_id = jwt_data.get('user_id', 0)
        self.mumble_if_false(
            user_id != 0, "JWT not found in the cookie"
        )
        return user_id


if __name__ == "__main__":
    NoteChecker().run()
