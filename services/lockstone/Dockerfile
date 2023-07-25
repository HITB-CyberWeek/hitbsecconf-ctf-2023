FROM ubuntu:23.04

RUN useradd -m -u 10000 lockstone

RUN apt-get update && apt-get install -y nodejs

RUN apt-get install -y npm

WORKDIR /home/lockstone/
CMD ["./start.sh"]
