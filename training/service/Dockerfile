FROM golang:1.20.5

WORKDIR /app

COPY go.mod .
COPY go.sum .
COPY main.go .
COPY rsa.go .

RUN go get .
RUN go build .

RUN rm go.mod go.sum main.go rsa.go

CMD ["go", "run", "."]
