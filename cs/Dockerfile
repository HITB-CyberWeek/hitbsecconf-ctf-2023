FROM mcr.microsoft.com/dotnet/sdk:7.0 AS build-dotnet-checkers

WORKDIR /app/places
COPY checkers/places/src/ ./
RUN dotnet publish -c release -o ./publish

WORKDIR /app/spaces
COPY checkers/spaces/src/ ./
RUN dotnet publish -c release -o ./publish


FROM ghcr.io/hackerdom/ctf-scoreboard-client:master AS scoreboard


FROM ghcr.io/hackerdom/checksystem:master

COPY --from=scoreboard /scoreboard/build /scoreboard
ENV CS_STATIC=/scoreboard

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip nodejs npm

# Install dotnet runtime (https://learn.microsoft.com/en-us/dotnet/core/install/linux-debian)
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
RUN wget https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \ 
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y --no-install-recommends dotnet-runtime-7.0

COPY checkers/funding/package*.json /app/checkers/funding/
RUN /bin/bash -c "cd /app/checkers/funding; npm ci"

RUN pip3 install requests gornilo --break-system-packages

# Config
COPY cs/cs.conf /app/c_s.conf

# Copy checkers and install dependencies

COPY checkers/training     /app/checkers/training
COPY checkers/passmgr      /app/checkers/passmgr
COPY checkers/spaces       /app/checkers/spaces
COPY --from=build-dotnet-checkers /app/spaces/publish/ /app/checkers/spaces/src/bin/Release/net7.0/publish
COPY checkers/lockstone    /app/checkers/lockstone
COPY checkers/godeeper     /app/checkers/godeeper
# COPY checkers/pure         /app/checkers/pure
COPY checkers/funding      /app/checkers/funding
COPY checkers/keys         /app/checkers/keys
COPY checkers/places       /app/checkers/places
COPY --from=build-dotnet-checkers /app/places/publish/ /app/checkers/places/src/bin/Release/net7.0/publish
COPY checkers/docs         /app/checkers/docs
COPY checkers/tokenourcer  /app/checkers/tokenourcer
RUN pip install -r /app/checkers/tokenourcer/requirements.txt --break-system-packages
COPY checkers/notes        /app/checkers/notes
RUN pip install -r /app/checkers/notes/requirements.txt --break-system-packages
