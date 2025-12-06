# Docker 배포 가이드

## 사전 준비

### 1. SSL 인증서 생성
```bash
cd database
./create_cert.sh
```

이 스크립트는 다음 인증서들을 생성합니다:
- `MyRootCA.crt` - Root CA 인증서
- `pg-server.crt`, `pg-server.key` - PostgreSQL 서버 인증서
- `backend-client.crt`, `backend-client.key` - 백엔드 클라이언트 인증서
- `admin-console.crt`, `admin-console.key` - 관리자 콘솔 인증서

### 2. 환경 변수 설정
```bash
cp .env.example .env
nano .env
```

`.env` 파일에서 다음 값들을 설정:
```
POSTGRES_PASSWORD=your_secure_password
```

## Docker 빌드 및 실행

### 전체 스택 시작
```bash
docker compose up -d
```

### 개별 서비스 시작
```bash
# PostgreSQL만
docker compose up -d postgres

# Redis만
docker compose up -d redis

# 백엔드만
docker compose up -d backend

# 프론트엔드만
docker compose up -d frontend
```

### 로그 확인
```bash
# 모든 서비스
docker compose logs -f

# 특정 서비스
docker compose logs -f backend
docker compose logs -f postgres
```

### 서비스 중지
```bash
docker compose down
```

### 서비스 중지 및 볼륨 삭제 (데이터 초기화)
```bash
docker compose down -v
```

## 초기 데이터베이스 설정

컨테이너가 처음 시작되면 `init_schema.sql`이 자동으로 실행됩니다.

추가 설정이 필요한 경우:
```bash
# PostgreSQL 컨테이너 접속
docker exec -it trade-everything-db psql -U postgres -d tedb

# 또는 호스트에서 직접 연결
psql -h localhost -U postgres -d tedb
```

## 서비스 접속 주소

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8001
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 헬스체크

각 서비스의 상태 확인:
```bash
docker compose ps
```

## 트러블슈팅

### PostgreSQL SSL 인증서 권한 문제
```bash
# 컨테이너 내부에서 권한 확인
docker exec -it trade-everything-db ls -la /certs
```

### 백엔드가 DB에 연결 안 됨
```bash
# 백엔드 로그 확인
docker compose logs backend

# PostgreSQL 연결 테스트
docker exec -it trade-everything-backend psql \
  "host=postgres dbname=tedb user=backend_user \
   sslmode=verify-full \
   sslrootcert=/app/certs/MyRootCA.crt \
   sslcert=/app/certs/backend-client.crt \
   sslkey=/app/certs/backend-client.key"
```

### 프론트엔드 빌드 실패
```bash
# 프론트엔드 컨테이너 재빌드
docker compose build --no-cache frontend
```

## 프로덕션 배포 시 추가 고려사항

### 1. 환경 변수 보안
실제 배포 시에는 `.env` 파일을 안전하게 관리하세요.

### 2. 볼륨 백업
```bash
# PostgreSQL 데이터 백업
docker exec trade-everything-db pg_dump -U postgres tedb > backup.sql

# 볼륨 백업
docker run --rm -v trade-everything_postgres_data:/data \
  -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

### 4. 리소스 제한
`docker-compose.yml`에 리소스 제한 추가:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## 업데이트 배포

```bash
# 최신 코드 가져오기
git pull

# 이미지 재빌드
docker compose build

# 서비스 재시작
docker compose up -d

# 또는 한 번에
docker compose up -d --build
```

## 버전 정보

- Python: 3.12
- PostgreSQL: 16
- Redis: 7
- React: 19
- Node.js: 20 (빌드 시)
