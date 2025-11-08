-- DB 생성
CREATE DATABASE tedb;

-- 사용자 생성
CREATE USER teuser WITH LOGIN;
CREATE USER teadmin WITH LOGIN SUPERUSER;

-- DB 권한 부여
\c tedb
GRANT ALL PRIVILEGES ON DATABASE tedb TO teuser;
GRANT ALL PRIVILEGES ON SCHEMA public TO teuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO teuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO teuser;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO teuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO teuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO teuser;

-- 사용자 확인
SELECT 
    usename AS username,
    usesuper AS is_superuser,
    usecreatedb AS can_create_db,
    passwd IS NOT NULL AS has_password
FROM pg_user
WHERE usename IN ('teuser', 'teadmin');