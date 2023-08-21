#!/bin/bash

echo "Creating the CA Key and Certificate"
openssl genrsa -aes256 -out ca.key 4096
openssl req -new -x509 -days 365 -sha256 -key ca.key -out ca.crt -subj "/CN=Pure CA"

echo "Creating the Server Key and CSR"
openssl genrsa -out server.key 4096
openssl req -new -key server.key -out server.csr -subj "/CN=Pure Server"

echo "Creating the Client Key and CSR"
openssl genrsa -out client.key 4096
openssl req -new -key client.key -out client.csr -subj "/CN=Pure Client"

echo "Creating the Server Certificate"
openssl x509 -req -days 365 -sha256 -in server.csr -CA ca.crt -CAkey ca.key -set_serial 01 -out server.crt && rm server.csr

echo "Creating the Client Certificate"
openssl x509 -req -days 365 -sha256 -in client.csr -CA ca.crt -CAkey ca.key -set_serial 01 -out client.crt && rm client.csr
