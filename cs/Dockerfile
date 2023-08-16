FROM ghcr.io/hackerdom/ctf-scoreboard-client:master AS scoreboard

FROM ghcr.io/hackerdom/checksystem:master

COPY --from=scoreboard /scoreboard/build /scoreboard
ENV CS_STATIC=/scoreboard

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip
RUN pip3 install gornilo --break-system-packages

# Config
COPY cs/cs.conf /app/c_s.conf

# Checkers

COPY checkers/docs /app/checkers/docs
