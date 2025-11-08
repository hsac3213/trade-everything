## DB 서버 인증서 경로 지정
```sh
# pg-server.key의 소유자는 postgress 또는 root로 설정해야 함
sudo chown postgres ~/trade-everything/database/certs/pg-server.key
# pg-server.key의 권한 설정 필요
sudo chmod 600 ~/trade-everything/database/certs/pg-server.key
sudo nano /etc/postgresql/13/main/postgresql.conf
```
다음 내용 추가:
...
ssl = on
ssl_ca_file = '~/trade-everything/database/certs/MyRootCA.crt'
ssl_cert_file = '~/trade-everything/database/certs/pg-server.crt'
ssl_key_file = '~/trade-everything/database/certs/pg-server.key'
...

## DB 서버 인증서 규칙 설정

```sh
sudo nano /etc/postgresql/13/main/pg_hba.conf

```
다음 내용 추가:
```
hostssl         all              all             0.0.0.0/0      cert clientcert=verify-full map=cert_map
```
그리고
```sh
sudo nano /etc/postgresql/13/main/pg_ident.conf

```
다음 내용 추가:
```
cert_map        backend-service              teuser
cert_map        backend.tradeeverything.local teuser

cert_map        admin-console                teadmin
```

## DB 서버 재시작
```sh
sudo systemctl restart postgresql
```

## (!) 로그 확인 방법
```sh
tail -F /var/log/postgresql/postgresql-13-main.log
```