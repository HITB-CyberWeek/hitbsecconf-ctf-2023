FROM ghcr.io/hackerdom/ctf-scoreboard-client:master AS scoreboard

FROM ghcr.io/hackerdom/checksystem:master

COPY --from=scoreboard /scoreboard/build /scoreboard
ENV CS_STATIC=/scoreboard

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip nodejs npm

COPY checkers/funding/package*.json /app/checkers/funding/
RUN /bin/bash -c "cd /app/checkers/funding; npm ci"

RUN pip3 install requests gornilo --break-system-packages

# Config
COPY cs/cs.conf /app/c_s.conf

# Copy checkers and install dependencies

COPY checkers/passmgr      /app/checkers/passmgr
COPY checkers/spaces       /app/checkers/spaces
COPY checkers/lockstone    /app/checkers/lockstone
COPY checkers/godeeper     /app/checkers/godeeper
# COPY checkers/pure         /app/checkers/pure
COPY checkers/funding      /app/checkers/funding
COPY checkers/keys         /app/checkers/keys
COPY checkers/places       /app/checkers/places
# COPY checkers/docs         /app/checkers/docs
# COPY checkers/tokenourcer  /app/checkers/tokenourcer
COPY checkers/notes        /app/checkers/notes
