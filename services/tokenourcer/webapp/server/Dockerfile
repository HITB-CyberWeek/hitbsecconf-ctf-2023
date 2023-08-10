FROM python:3.10-alpine
WORKDIR /flask
COPY . /flask
RUN pip install -r requirements.txt
ENTRYPOINT ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "-c", "gc_config.py", "--error-logfile", "logs/app.error.log", "main:app"]
