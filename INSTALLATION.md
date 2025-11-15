# 공통
1. 홈 디렉터리에 trade-everything 레포지토리 clone.
2. trade-everything 디렉터리로 이동.

# Frontend
```sh
sudo apt install npm
cd ./frontend
npm install
```

# Backend
```sh
sudo apt install python3.12-venv
# 파이썬 가상환경 생성
python3 -m venv .trvenv
source ~/trade-everything/.trvenv/bin/activate
pip install -r requirements.txt

# Redis 설치
sudo apt install redis-server
```

# Database
```sh
# PostgreSQL 설치
sudo apt install postgresql postgresql-contrib
# 사용자 및 데이터베이스 생성
sudo -u postgres psql -f ./database/init_db.sql
# 데이터베이스 스키마 생성
sudo -u postgres psql -d tedb -f ./database/init_schema.sql
# 데이터베이스 접속을 위한 인증서 생성
cd database
sh ./create_cert.sh
cd ..
```
인증서 설정 방법은 **./database** 디렉터리 내의 **README.md** 참고

# Optional

# 테스트 환경
OS : Ubuntu 24.04.3 LTS
Processor : x86_64