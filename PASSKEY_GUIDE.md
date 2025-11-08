# Passkey 기반 인증 시스템 구현 가이드

### 인증 흐름

#### 1. 회원가입 (Registration)
```
Frontend                Backend                PostgreSQL
   │                       │                       │
   │──── /register/begin ──►│                       │
   │                       │                       │
   │◄─── options ──────────│                       │
   │                       │                       │
   │ [User creates        │                       │
   │  passkey]            │                       │
   │                       │                       │
   │──── /register/complete─►│                       │
   │                       │                       │
   │                       │──── INSERT user ─────►│
   │                       │                       │
   │                       │◄─── user_id ──────────│
   │                       │                       │
   │                       │──── INSERT credential ►│
   │                       │                       │
   │◄─── verified ─────────│                       │
```

#### 2. 로그인 (Authentication)
```
Frontend                Backend                PostgreSQL          Redis
   │                       │                       │               │
   │──── /login/begin ─────►│                       │               │
   │                       │                       │               │
   │                       │──── SELECT user ─────►│               │
   │                       │                       │               │
   │                       │◄─── credentials ──────│               │
   │                       │                       │               │
   │◄─── options ──────────│                       │               │
   │                       │                       │               │
   │ [User uses          │                       │               │
   │  passkey]            │                       │               │
   │                       │                       │               │
   │──── /login/complete ───►│                       │               │
   │                       │                       │               │
   │                       │──── VERIFY credential ►│               │
   │                       │                       │               │
   │                       │──── UPDATE sign_count ►│               │
   │                       │                       │               │
   │                       │──── CREATE JWT ───────────────────────►│
   │                       │                       │               │
   │◄─── JWT tokens ───────│                       │               │
```

---

## 🚀 설치 및 설정

### 1. 패키지 설치

#### Backend (Python)
```bash
pip install -r requirements.txt
```

필수 패키지:
- `webauthn==2.2.0` - WebAuthn 서버 구현
- `python-jose[cryptography]` - JWT 생성/검증
- `redis` - 세션 관리
- `psycopg2-binary` - PostgreSQL 연결

#### Frontend (React)
```bash
cd frontend
npm install @simplewebauthn/browser
```

### 2. 데이터베이스 설정

```bash
# PostgreSQL 데이터베이스 생성
createdb trade_everything

# 스키마 적용
psql -d trade_everything -f database/passkey_schema.sql
```

## 💻 코드 구조

### Backend (FastAPI)

#### 1. **auth.py** - Passkey 엔드포인트

```python
# 회원가입 시작
POST /auth/passkey/register/begin
{
  "username": "john_doe"
}

# 회원가입 완료
POST /auth/passkey/register/complete
{
  "username": "john_doe",
  "attestationResponse": {...}
}

# 로그인 시작
POST /auth/passkey/login/begin
{
  "username": "john_doe"
}

# 로그인 완료 (JWT 토큰 반환)
POST /auth/passkey/login/complete
{
  "username": "john_doe",
  "assertionResponse": {...}
}
→ Response: {
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 900
}
```

#### 2. **session_manager.py** - JWT + Redis 세션 관리

주요 기능:
- JWT 토큰 생성/검증
- Redis 블랙리스트 (강제 로그아웃)
- 세션 핑거프린트 (하이재킹 방지)

#### 3. **auth_dependency.py** - 인증 미들웨어

```python
@router.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    # user 정보 자동으로 주입
    return {"user_id": user["user_id"]}
```

### Frontend (React/TypeScript)

#### 1. **PasskeyAuth.tsx** - Passkey 로직

```typescript
// 회원가입
const result = await handlePasskeyRegister("username");

// 로그인 (JWT 토큰 반환)
const result = await handlePasskeyLogin("username");
if (result.success && result.tokens) {
  // 토큰 저장
  AuthService.setTokens(result.tokens);
}
```

#### 2. **AuthService.ts** - 세션 관리

```typescript
// Passkey 로그인 (토큰 자동 저장)
await SecureAuthService.loginWithPasskey("username");

// 인증된 API 호출
const response = await authenticatedFetch("/api/data");

// 로그아웃
await SecureAuthService.logout();
```

#### 3. **Login.tsx** - 로그인 UI

```typescript
<button onClick={onLoginClick}>
  Login with Passkey
</button>

<button onClick={onRegisterClick}>
  Register with Passkey
</button>
```

---

## 🔐 보안 기능

### 1. Passkey (WebAuthn)
- **피싱 방지**: Origin 검증으로 가짜 사이트 차단
- **중간자 공격 방지**: Challenge-Response 방식
- **Replay 방지**: Sign count 검증

### 2. JWT + Redis Hybrid
- **짧은 수명**: Access Token 15분
- **강제 로그아웃**: Redis 블랙리스트
- **자동 갱신**: 만료 2분 전 자동 갱신

### 3. 세션 핑거프린트
- **IP + User-Agent** 검증
- **하이재킹 감지**: 불일치 시 모든 세션 무효화

### 4. 메모리 토큰 저장
- **XSS 방지**: LocalStorage 대신 메모리 사용
- **자동 정리**: 페이지 닫으면 토큰 삭제

---

## 📖 사용 예제

### 1. 회원가입

```typescript
import SecureAuthService from './AuthService';

// Passkey 등록
const result = await SecureAuthService.registerWithPasskey("john_doe");

if (result.success) {
  console.log("✅ Registration successful!");
  // 이제 로그인 가능
} else {
  console.error("❌", result.message);
}
```

### 2. 로그인

```typescript
// Passkey 로그인 (JWT 토큰 자동 저장)
try {
  await SecureAuthService.loginWithPasskey("john_doe");
  console.log("✅ Login successful!");
  // 메인 페이지로 이동
  navigate("/main");
} catch (error) {
  console.error("❌ Login failed:", error);
}
```

### 3. 인증된 API 호출

```typescript
import { authenticatedFetch } from './AuthService';

// 자동으로 Authorization 헤더 추가
const response = await authenticatedFetch("/api/user/settings");
const data = await response.json();

// 401 에러 시 자동 토큰 갱신 시도
```

### 4. 로그아웃

```typescript
// 현재 디바이스만 로그아웃
await SecureAuthService.logout();

// 모든 디바이스에서 로그아웃
await SecureAuthService.logoutAllDevices();
```

---

## 🧪 테스트

### 1. 서버 실행

```bash
# Backend
cd api_broker
python run_server.py

# Frontend
cd frontend
npm run dev
```

### 2. 브라우저 접속

```
http://localhost:5173
```

### 3. 회원가입 테스트

1. Username 입력 (예: `testuser`)
2. "Register with Passkey" 클릭
3. 브라우저 생체인증 프롬프트 확인
4. 지문/Face ID로 인증
5. ✅ "Registration successful!" 메시지 확인

### 4. 로그인 테스트

1. 같은 Username 입력
2. "Login with Passkey" 클릭
3. 생체인증 수행
4. ✅ 자동으로 메인 페이지 이동

### 5. API 테스트 (curl)

```bash
# 로그인
curl -X POST http://localhost:8001/auth/passkey/login/complete \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "assertionResponse": {...}
  }'

# 토큰 저장
TOKEN="eyJ..."

# 보호된 리소스 접근
curl -X GET http://localhost:8001/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🛠️ 트러블슈팅

### 1. "Passkey not supported"
→ **해결**: HTTPS 또는 localhost에서만 작동합니다.

### 2. "User not found"
→ **해결**: 먼저 회원가입을 진행하세요.

### 3. "Challenge not found"
→ **해결**: 등록/로그인을 처음부터 다시 시작하세요.

### 4. Redis 연결 오류
```bash
# Redis 실행 확인
redis-cli ping
# PONG 응답이 나와야 함
```

### 5. PostgreSQL 연결 오류
```bash
# 환경변수 확인
echo $DB_ADDRESS
echo $DB_PASSWORD

# 데이터베이스 존재 확인
psql -l | grep trade_everything
```

---

## 📊 데이터베이스 스키마

### users 테이블
```sql
user_id       SERIAL PRIMARY KEY
username      VARCHAR(100) UNIQUE NOT NULL
created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
last_login    TIMESTAMP
```

### passkey_credentials 테이블
```sql
credential_id VARCHAR(500) PRIMARY KEY  -- Base64 encoded
user_id       INTEGER REFERENCES users(user_id)
public_key    TEXT NOT NULL              -- Base64 encoded
sign_count    BIGINT DEFAULT 0           -- Replay attack prevention
created_at    TIMESTAMP
last_used     TIMESTAMP
```

---

## 🔄 세션 관리 상세

### JWT 토큰 구조

```json
{
  "user_id": 123,
  "username": "john_doe",
  "jti": "unique_token_id",
  "exp": 1234567890,
  "iat": 1234567000,
  "type": "access"
}
```

### Redis 저장 구조

```
session:{token}           → 세션 데이터 (15분 TTL)
blacklist:{jti}           → 블랙리스트 (만료 시까지)
user_sessions:{user_id}   → 활성 세션 목록
```

### 세션 검증 순서

1. **JWT 디코딩 및 서명 검증**
2. **블랙리스트 확인** (로그아웃된 토큰인지)
3. **Redis 세션 존재 확인**
4. **핑거프린트 검증** (IP + User-Agent)
5. **세션 갱신** (슬라이딩 윈도우)

---

## 🚀 프로덕션 배포 체크리스트

- [ ] SECRET_KEY를 환경변수로 변경
- [ ] HTTPS 적용 (WebAuthn 필수)
- [ ] RP_ID를 실제 도메인으로 변경
- [ ] RP_ORIGIN을 실제 URL로 변경
- [ ] PostgreSQL 접속 정보 보안
- [ ] Redis 비밀번호 설정
- [ ] CORS 도메인 제한
- [ ] Rate Limiting 추가
- [ ] 로깅 및 모니터링 설정

---

## 📚 참고 자료

- [WebAuthn Guide](https://webauthn.guide/)
- [SimpleWebAuthn Docs](https://simplewebauthn.dev/)
- [FIDO2 Specification](https://fidoalliance.org/fido2/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)

---

## 💡 추가 기능 아이디어

1. **다중 Passkey 지원**: 여러 디바이스 등록
2. **Passkey 관리**: 등록된 디바이스 목록 및 삭제
3. **백업 인증**: 이메일 OTP 백업
4. **디바이스 이름**: "iPhone", "MacBook" 등 표시
5. **로그인 알림**: 새 디바이스 로그인 시 알림

---

## ❓ FAQ

**Q: 비밀번호 복구는 어떻게 하나요?**
A: Passkey는 비밀번호가 없습니다. Passkey 분실 시 이메일 인증 등 백업 방법이 필요합니다.

**Q: 여러 디바이스에서 사용 가능한가요?**
A: 네, 각 디바이스에서 Passkey를 등록하면 됩니다.

**Q: 지문인식이 없는 PC에서는?**
A: Windows Hello, USB 보안키 등을 사용할 수 있습니다.

**Q: Safari/Chrome 모두 지원하나요?**
A: 네, 모든 최신 브라우저가 WebAuthn을 지원합니다.
