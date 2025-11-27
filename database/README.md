## 구버전 라이브러리(libpq-10.dll) 사용 시 접속이 안될 수 있음!

## **./database** 디렉터리에서 수행
```sh
# 인증서 복사

# 아래 "16"은 버전에 따라 다를 수 있음!!!
sudo cp ./certs/MyRootCA.crt /etc/postgresql/16/main/MyRootCA.crt
sudo cp ./certs/pg-server.crt /etc/postgresql/16/main/pg-server.crt
sudo cp ./certs/pg-server.key /etc/postgresql/16/main/pg-server.key

# pg-server.key의 소유자는 postgress 또는 root로 설정해야 함
sudo chown postgres /etc/postgresql/16/main/pg-server.key
# pg-server.key의 권한 설정 필요
sudo chmod 600 /etc/postgresql/16/main/pg-server.key
```

## DB 서버 인증서 경로 지정
```sh
# 아래 "16"은 버전에 따라 다를 수 있음
sudo nano /etc/postgresql/16/main/postgresql.conf
```

파일 하단에 다음 내용 추가:<br>
**[중요] 아래 "16"은 버전에 따라 다를 수 있음!!!**
```
ssl = on
ssl_ca_file = '/etc/postgresql/16/main/MyRootCA.crt'
ssl_cert_file = '/etc/postgresql/16/main/pg-server.crt'
ssl_key_file = '/etc/postgresql/16/main/pg-server.key'
```

아래 내용들은 주석 처리(#) 해주어야 함:
```
ssl = on
#ssl_ca_file = ''
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
#ssl_crl_file = ''
#ssl_crl_dir = ''
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'
```
to
```
ssl = on
#ssl_ca_file = ''
#ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
#ssl_crl_file = ''
#ssl_crl_dir = ''
#ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'
```

사용자 이름 확인 방법
```sh
echo $USER
```

PostgreSQL 버전 확인 방법
```sh
psql --version
# 출력 예 : psql (PostgreSQL) 16.10 (Ubuntu 16.10-0ubuntu0.24.04.1)
```

## DB 서버 인증서 규칙 설정

```sh
# 아래 "16"은 버전에 따라 다를 수 있음
sudo nano /etc/postgresql/16/main/pg_hba.conf
```
다음 내용 추가:
```
hostssl         all              all             0.0.0.0/0      cert clientcert=verify-full map=cert_map
```
그리고
```sh
# 아래 "16"은 버전에 따라 다를 수 있음
sudo nano /etc/postgresql/16/main/pg_ident.conf
```
다음 내용 추가:
```
cert_map        backend-service              teuser
cert_map        backend.tradeeverything.local teuser

cert_map        admin-console                teadmin
```

## 외부 접속 허용(optional)
```sh
sudo nano /etc/postgresql/16/main/postgresql.conf
```

다음 내용 추가:
```
listen_addresses = '*'
```

## DB 서버 재시작
```sh
sudo systemctl restart postgresql
```

## (!) 로그 확인 방법
```sh
# 아래 "16"은 버전에 따라 다를 수 있음
tail -F /var/log/postgresql/postgresql-16-main.log
```