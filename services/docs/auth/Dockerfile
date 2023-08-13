FROM python:3.11

RUN pip3 install fastapi uvicorn[standard] psycopg redis

WORKDIR /app
COPY . /app

CMD ["uvicorn", "--host", "0.0.0.0", "auth:app"]
