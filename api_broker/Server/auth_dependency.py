"""
FastAPI 인증 의존성
JWT + Redis 세션 검증 및 핑거프린트 확인
"""
from .session_manager import SecureSessionManager
from .redis_manager import RedisManager
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from datetime import datetime

# HTTPBearer 보안 스키마
security = HTTPBearer()

# 전역 세션 관리자 인스턴스
redis_manager = RedisManager()
session_manager = SecureSessionManager(redis_manager.redis_client)

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    현재 사용자 정보 가져오기 (HTTP 요청용)
    
    검증 절차:
    1. JWT 토큰 검증 + 블랙리스트 확인
    2. Redis 세션 확인
    3. 세션 핑거프린트 검증 (세션 하이재킹 방지)
    4. 세션 갱신 (슬라이딩 윈도우)
    
    Args:
        request: FastAPI Request 객체
        credentials: HTTPBearer에서 추출한 인증 정보
    
    Returns:
        사용자 정보 딕셔너리
    
    Raises:
        HTTPException: 인증 실패 시
    """
    token = credentials.credentials
    
    # 1️⃣ JWT 검증 + 블랙리스트 확인
    payload = session_manager.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 2️⃣ Redis 세션 확인
    session_data = session_manager.get_session(token)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 3️⃣ 세션 핑거프린트 검증 (세션 하이재킹 방지)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    if not session_manager.verify_session_fingerprint(token, client_ip, user_agent):
        # 의심스러운 활동 감지 → 모든 세션 무효화
        user_id = payload.get("user_id")
        session_manager.revoke_all_user_sessions(user_id)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session hijacking detected. All sessions have been revoked for security.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 4️⃣ 세션 갱신 (슬라이딩 윈도우)
    session_manager.refresh_session(token)
    
    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "jti": payload.get("jti"),
        "session": session_data,
        "token": token  # 로그아웃 시 필요
    }


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    선택적 사용자 정보 가져오기 (인증 선택적)
    
    Args:
        request: FastAPI Request 객체
        credentials: HTTPBearer에서 추출한 인증 정보 (없을 수 있음)
    
    Returns:
        사용자 정보 딕셔너리 또는 None
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None

async def get_user_from_token(token) -> Dict[str, Any]:    
    # 1️⃣ JWT 검증 + 블랙리스트 확인
    payload = session_manager.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 2️⃣ Redis 세션 확인
    session_data = session_manager.get_session(token)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 4️⃣ 세션 갱신 (슬라이딩 윈도우)
    session_manager.refresh_session(token)
    
    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "jti": payload.get("jti"),
        "session": session_data,
        "token": token  # 로그아웃 시 필요
    }