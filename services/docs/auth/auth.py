from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import Optional

import hmac
import hashlib
import os
import psycopg
from psycopg import sql
import redis

db = psycopg.connect(
    host="pg",
    user="postgres",
    password=os.getenv('POSTGRES_PASSWORD'),
    dbname="docs"
)
r = redis.from_url("redis://redis:6379")

class UserInfo(BaseModel):
    login: str
    password: str
    org: Optional[str] = None

app = FastAPI()

@app.post("/register")
def register(ri: UserInfo, response: Response):
    with db.cursor() as cursor:
        try:
            cursor.execute(
                """insert into users (login, pass, org)
                values (%(login)s, %(password)s, %(org)s)
                returning id""",
                ri.model_dump()
            )
            user_id = cursor.fetchone()
            cursor.execute(
                sql.SQL("create role {} with login password {} in role docs_user").
                format(sql.Identifier(ri.login), ri.password)
            )
            r.set(ri.login, f"postgresql://{ri.login}:{ri.password}@pg:5432/docs")
            db.commit()
        except Exception as e:
            db.rollback()
            response.status_code = 400
            return {"error": str(e)}

    return {"login": ri.login, "user_id": user_id[0]}

@app.post("/login")
def login(li: UserInfo, response: Response):
    with db.cursor() as cursor:
        try:
            cursor.execute(
                "select id from users where login = %(login)s and pass = %(password)s",
                li.model_dump()
            )
            user_id = cursor.fetchone()
            if user_id[0]:
                sign = hmac.new(
                    os.getenv('DOCS_SECRET').encode("UTF-8"),
                    li.login.encode("UTF-8"),
                    hashlib.sha1
                ).hexdigest()
                response.set_cookie(
                    key="docs_session",
                    value=li.login + "--" + sign,
                    httponly=True
                )
                response.status_code = 204
                return
        except Exception as e:
            db.rollback()
        finally:
            db.rollback()
    response.status_code = 400
    return

@app.post("/logout")
def logout(response: Response):
    response.delete_cookie("docs_session")
    response.status_code = 204
    return
