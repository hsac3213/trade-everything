"""
보안 강화 세션 관리자
JWT + Redis 블랙리스트 + 세션 핑거프린트를 사용한 Hybrid 세션 관리
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import hashlib
import json
from jose import JWTError, jwt

# JWT 설정

# 테스트 환경이므로 랜덤 값 사용
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"

# Access 토큰 만료 시간(분 단위) 지정
ACCESS_TOKEN_EXPIRE_MINUTES = 15
# Refresh 토큰 만료 시간(일 단위) 지정
REFRESH_TOKEN_EXPIRE_DAYS = 7

class SecureSessionManager:
    def __init__(self, redis_client):
        self.redis_client = redis_client
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        JWT Access Token 생성 (최소 클레임만 포함)
        
        Args:
            data: 토큰에 포함할 데이터 (user_id 필수)
        
        Returns:
            생성된 JWT 토큰
        """
        to_encode = {
            "user_id": data["user_id"],
            "jti": secrets.token_urlsafe(16),  # JWT ID (고유 식별자)
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        # 선택적 필드 추가
        if "email" in data:
            to_encode["email"] = data["email"]
        
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        JWT Refresh Token 생성
        
        Args:
            data: 토큰에 포함할 데이터 (user_id 필수)
        
        Returns:
            생성된 Refresh 토큰
        """
        to_encode = {
            "user_id": data["user_id"],
            "jti": secrets.token_urlsafe(16),
            "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        JWT 검증 + 블랙리스트 확인
        
        Args:
            token: 검증할 JWT 토큰
        
        Returns:
            토큰 payload 또는 None
        
        Raises:
            JWTError: 토큰 검증 실패 시
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # 블랙리스트 확인 (로그아웃된 토큰)
            if self.is_token_blacklisted(payload.get("jti")):
                return None
            
            return payload
        except JWTError:
            return None
    
    def blacklist_token(self, jti: str, exp: datetime) -> None:
        """
        토큰을 블랙리스트에 등록 (강제 무효화)
        
        Args:
            jti: JWT ID
            exp: 토큰 만료 시간
        """
        ttl = int((exp - datetime.utcnow()).total_seconds())
        if ttl > 0:
            self.redis_client.set(name=f"blacklist:{jti}", value="1", ex=ttl)
            print(f"🔒 Token blacklisted: {jti}")
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """
        토큰이 블랙리스트에 있는지 확인
        
        Args:
            jti: JWT ID
        
        Returns:
            블랙리스트 포함 여부
        """
        return self.redis_client.exists(f"blacklist:{jti}") > 0
    
    def save_session(
        self,
        user_id: int,
        token: str,
        ip: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        세션 저장 + 디바이스 핑거프린트
        
        Args:
            user_id: 사용자 ID
            token: Access Token
            ip: 클라이언트 IP
            user_agent: User-Agent 헤더
            metadata: 추가 메타데이터
        """
        # 디바이스 핑거프린트 생성
        fingerprint = hashlib.sha256(
            f"{ip}:{user_agent}".encode()
        ).hexdigest()
        
        session_data = {
            "user_id": user_id,
            "fingerprint": fingerprint,
            "ip": ip,
            "user_agent": user_agent,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if metadata:
            session_data.update(metadata)
        
        # Redis에 세션 저장
        session_key = f"session:{token}"
        self.redis_client.set(
            name=session_key,
            value=json.dumps(session_data),
            ex=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # 사용자별 활성 세션 추적
        self.redis_client.sadd(f"user_sessions:{user_id}", token)
        print(f"✅ Session saved: user_id={user_id}, ip={ip}")
    
    def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Redis에서 세션 조회
        
        Args:
            token: Access Token
        
        Returns:
            세션 데이터 또는 None
        """
        session_key = f"session:{token}"
        session_data = self.redis_client.get(name=session_key)
        
        if session_data:
            return json.loads(session_data)
        return None
    
    def verify_session_fingerprint(
        self,
        token: str,
        ip: str,
        user_agent: str
    ) -> bool:
        """
        세션 핑거프린트 검증 (세션 하이재킹 방지)
        
        Args:
            token: Access Token
            ip: 현재 요청 IP
            user_agent: 현재 User-Agent
        
        Returns:
            핑거프린트 일치 여부
        """
        session_data = self.get_session(token)
        
        if not session_data:
            return False
        
        current_fingerprint = hashlib.sha256(
            f"{ip}:{user_agent}".encode()
        ).hexdigest()
        
        return session_data.get("fingerprint") == current_fingerprint
    
    def refresh_session(self, token: str) -> None:
        """
        세션 만료 시간 갱신 (슬라이딩 윈도우)
        
        Args:
            token: Access Token
        """
        session_key = f"session:{token}"
        self.redis_client.expire(
            name=session_key,
            time=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
    
    def delete_session(self, token: str, user_id: int) -> None:
        """
        세션 삭제 (로그아웃)
        
        Args:
            token: Access Token
            user_id: 사용자 ID
        """
        session_key = f"session:{token}"
        self.redis_client.delete(name=session_key)
        
        # 사용자 세션 목록에서 제거
        self.redis_client.srem(f"user_sessions:{user_id}", token)

        print(f"🔌 Session deleted: user_id={user_id}")
    
    def revoke_all_user_sessions(self, user_id: int) -> int:
        """
        사용자의 모든 세션 강제 무효화
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            무효화된 세션 개수
        """
        sessions_key = f"user_sessions:{user_id}"
        tokens = self.redis_client.smembers(sessions_key)
        
        count = 0
        for token in tokens:
            # 토큰 디코딩하여 jti 추출
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                self.blacklist_token(
                    payload["jti"],
                    datetime.fromtimestamp(payload["exp"])
                )
                count += 1
            except JWTError:
                pass
            
            # 세션 삭제
            self.redis_client.delete(f"session:{token}")
        
        # 세션 리스트 삭제
        self.redis_client.delete(sessions_key)
        
        print(f"🚫 All sessions revoked for user_id={user_id} (count={count})")
        return count
    
    def get_user_active_sessions(self, user_id: int) -> list:
        """
        사용자의 활성 세션 목록
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            활성 세션 리스트
        """
        sessions_key = f"user_sessions:{user_id}"
        tokens = self.redis_client.smembers(sessions_key)
        
        sessions = []
        for token in tokens:
            session_data = self.get_session(token)
            if session_data:
                sessions.append(session_data)
        
        return sessions