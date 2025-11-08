#!/bin/bash

rm -rf ./certs
mkdir ./certs

# RootCA 인증서 생성
openssl ecparam -name prime256v1 -genkey -noout -out ./certs/MyRootCA.key
openssl req -new -x509 -sha256 -days 3650 -key ./certs/MyRootCA.key -out ./certs/MyRootCA.crt \
-config ./cert_ca.conf

# DB 서버 인증서 생성
openssl ecparam -name prime256v1 -genkey -noout -out ./certs/pg-server.key
openssl req -new -sha256 -key ./certs/pg-server.key -out ./certs/pg-server.csr \
-config ./cert_db.conf

openssl x509 -req -in ./certs/pg-server.csr -CA ./certs/MyRootCA.crt -CAkey ./certs/MyRootCA.key \
-CAcreateserial -out ./certs/pg-server.crt -days 365 -sha256 \
-extfile ./cert_db.conf -extensions v3_req

# 백엔드 서버 인증서 생성
openssl ecparam -name prime256v1 -genkey -noout -out ./certs/backend-client.key
openssl req -new -sha256 -key ./certs/backend-client.key -out ./certs/backend-client.csr \
-config ./cert_backend.conf

openssl x509 -req -in ./certs/backend-client.csr -CA ./certs/MyRootCA.crt -CAkey ./certs/MyRootCA.key \
-CAcreateserial -out ./certs/backend-client.crt -days 365 -sha256 \
-extfile ./cert_backend.conf -extensions v3_extensions

# 관리자 인증서 생성(스키마 관리용)
openssl ecparam -name prime256v1 -genkey -noout -out ./certs/admin-console.key
openssl req -new -sha256 -key ./certs/admin-console.key -out ./certs/admin-console.csr \
-config ./cert_admin.conf

openssl x509 -req -in ./certs/admin-console.csr -CA ./certs/MyRootCA.crt -CAkey ./certs/MyRootCA.key \
-CAcreateserial -out ./certs/admin-console.crt -days 365 -sha256 \
-extfile ./cert_admin.conf -extensions v3_extensions