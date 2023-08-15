FROM ghcr.io/hackerdom/ctf-scoreboard-client:master AS scoreboard

FROM ghcr.io/hackerdom/checksystem:master

COPY --from=scoreboard /scoreboard/build /scoreboard
ENV CS_STATIC=/scoreboard

RUN pip3 install gornilo --break-system-packages

COPY cs/cs.conf /app/c_s.conf
