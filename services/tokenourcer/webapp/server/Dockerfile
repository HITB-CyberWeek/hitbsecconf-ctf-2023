FROM python:3.10-alpine

WORKDIR /app
COPY requirements.txt /app

RUN pip install -r requirements.txt
COPY . /app

ENTRYPOINT ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "--log-config", "log.conf", "main:app"]
