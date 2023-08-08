from fastapi import FastAPI, Response
from pydantic import BaseModel

import psycopg
from psycopg import sql
import redis
import os

db = psycopg.connect(
    host="pg",
    user="postgres",
    password=os.getenv('POSTGRES_PASSWORD'),
    dbname="docs"
)
r = redis.from_url("redis://redis:6379")

class RegisterInfo(BaseModel):
    login: str
    password: str
    org: str

app = FastAPI()

@app.post("/register")
def register(ri: RegisterInfo, response: Response):
    with db.cursor() as cursor:
        try:
            cursor.execute(
                "insert into users (login, pass, org) values (%(login)s, %(password)s, %(org)s)",
                ri.model_dump()
            )
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

    return {"status": "OK"}

@app.post("/login")
def login():
    pass

@app.post("/logout")
def logout():
    pass
