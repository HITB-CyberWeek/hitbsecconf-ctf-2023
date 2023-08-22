FROM golang:1.21.0 AS build
WORKDIR /app

COPY go.mod .
COPY go.sum .
RUN go mod download
COPY *.go ./

RUN go build -ldflags="-s -w" -o /app/places .


FROM golang:1.21.0
WORKDIR /app

RUN adduser -u 1000 --system --home /app --shell /usr/sbin/nologin --no-create-home --disabled-password usr

COPY ./start.sh .
COPY ./wwwroot/ wwwroot/
COPY --from=build /app/places /app/

RUN mkdir -p /app/data && mkdir -p /app/settings

CMD ["./start.sh"]
