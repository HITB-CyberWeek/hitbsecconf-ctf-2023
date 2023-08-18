FROM mcr.microsoft.com/dotnet/nightly/sdk:8.0-alpine AS build
WORKDIR /app

COPY ./src/ /app/
RUN dotnet publish -c release -o ./out


FROM mcr.microsoft.com/dotnet/nightly/aspnet:8.0-alpine
WORKDIR /app

RUN adduser -u 1000 --system --home /app --shell /usr/sbin/nologin --no-create-home --disabled-password usr

COPY ./start.sh .
COPY --from=build /app/out/ /app/

RUN mkdir -p /app/data && mkdir -p /app/settings
VOLUME /app/data

CMD ["./start.sh"]
