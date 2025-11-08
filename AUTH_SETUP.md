# Hybrid Session Management 구현 가이드

## 🚀 사용 방법

서버가 시작되면 다음 엔드포인트를 사용할 수 있습니다:
- `POST /auth/login` - 로그인
- `POST /auth/logout` - 로그아웃
- `POST /auth/logout-all` - 모든 디바이스에서 로그아웃
- `POST /auth/refresh` - 토큰 갱신
- `GET /auth/me` - 현재 사용자 정보
- `GET /auth/sessions` - 활성 세션 목록
- `GET /auth/health` - 헬스 체크

### Frontend 사용 예제

```typescript
import SecureAuthService from './AuthService';

// 로그인
try {
  await SecureAuthService.login('user@example.com', 'password');
  console.log('로그인 성공!');
} catch (error) {
  console.error('로그인 실패:', error);
}

// 현재 사용자 정보
const user = await SecureAuthService.getMe();
console.log('사용자:', user);

// 로그아웃
await SecureAuthService.logout();

// 인증이 필요한 API 호출
import { authenticatedFetch } from './AuthService';

const response = await authenticatedFetch('http://localhost:8001/api/data');
const data = await response.json();
```

## 🧪 테스트

### API 테스트 (curl)
```bash
# 로그인
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# 토큰 저장
TOKEN="eyJ..."

# 사용자 정보 조회
curl -X GET http://localhost:8001/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 로그아웃
curl -X POST http://localhost:8001/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

## 🛠️ 트러블슈팅

### Redis 연결 오류
```
❌ Redis connection failed
```
→ Redis 서버가 실행 중인지 확인: `redis-cli ping`

### Import 오류
```
Import "redis" could not be resolved
```
→ 패키지 재설치: `pip install -r requirements.txt`

### 401 Unauthorized
- 토큰이 만료되었거나 유효하지 않음
- `/auth/refresh`로 토큰 갱신 시도

## 📝 추가 구현 필요 사항

1. **PostgreSQL 연동**
   - `auth.py`의 TODO 부분 구현
   - 사용자 테이블 생성 및 연동

2. **비밀번호 재설정**
   - 이메일 인증 기반 비밀번호 재설정

3. **Passkey 통합**
   - WebAuthn API 연동
   - `Login.tsx`의 Passkey 기능 연동

4. **보안 강화 (선택사항)**
   - Rate Limiting
   - 2FA (TOTP)
   - Audit Log
