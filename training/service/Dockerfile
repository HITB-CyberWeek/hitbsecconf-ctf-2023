FROM golang:1.20.5

WORKDIR /app

COPY go.mod .
COPY go.sum .
COPY main.go .

RUN go get .

RUN rm go.mod go.sum main.go

CMD ["go", "run", "."]
