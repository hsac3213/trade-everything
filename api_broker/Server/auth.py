from .session_manager import SecureSessionManager, ACCESS_TOKEN_EXPIRE_MINUTES
from .auth_dependency import get_current_user
from .redis_manager import RedisManager
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime, timedelta
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import base64
import json
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor,
    AuthenticatorTransport,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier

# DB 서버 관련 환경변수 읽기
DB_HOST = os.environ.get("DB_HOST")
DB_ID = os.environ.get("DB_ID")
DB_NAME = "tedb"
DB_ROOT_CA_PATH = os.environ.get("DB_ROOT_CA_PATH")
DB_CERT_PATH = os.environ.get("DB_CERT_PATH")
DB_CERT_KEY_PATH = os.environ.get("DB_CERT_KEY_PATH")

"""
print(f"DB_HOST : {DB_HOST}")
print(f"DB_ID : {DB_ID}")
print(f"DB_ROOT_CA_PATH : {DB_ROOT_CA_PATH}")
print(f"DB_CERT_PATH : {DB_CERT_PATH}")
print(f"DB_CERT_KEY_PATH : {DB_CERT_KEY_PATH}")
"""

# 라우터 생성
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Passkey 설정
RP_ID = "localhost"
RP_NAME = "Trade Everything"
RP_ORIGIN = "http://localhost:5173"

# 세션 관리자 인스턴스
redis_manager = RedisManager()
session_manager = SecureSessionManager(redis_manager.redis_client)

# Challenge 관리 클래스
class ChallengeManager:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.prefix = "challenge:"
        self.ttl = 300  # 5분
    
    def save_challenge(self, key: str, challenge: bytes):
        """Challenge 저장 (SET with EX 사용)"""
        redis_key = f"{self.prefix}{key}"
        # SET with EX 옵션 사용 (권장 방식)
        self.redis_client.set(
            name=redis_key,
            value=challenge,
            ex=self.ttl  # expire in seconds
        )
        print(f"💾 Challenge saved: {key} (expires in {self.ttl}s)")
    
    def get_challenge(self, key: str) -> Optional[bytes]:
        """Challenge 조회"""
        redis_key = f"{self.prefix}{key}"
        try:
            challenge = self.redis_client.get(redis_key)
            if challenge:
                # 남은 TTL 확인 (디버깅용)
                ttl = self.redis_client.ttl(redis_key)
                challenge_len = len(challenge) if isinstance(challenge, bytes) else 0
                print(f"🔍 Challenge found: {key} (TTL: {ttl}s, length: {challenge_len} bytes)")
            else:
                print(f"⚠️ Challenge not found or expired: {key}")
            return challenge
        except Exception as e:
            print(f"❌ Error getting challenge: {type(e).__name__}: {str(e)}")
            raise
    
    def delete_challenge(self, key: str) -> int:
        """Challenge 삭제"""
        redis_key = f"{self.prefix}{key}"
        deleted = self.redis_client.delete(redis_key)
        if deleted:
            print(f"🗑️ Challenge deleted: {key}")
        return deleted
    
    def get_ttl(self, key: str) -> int:
        """Challenge의 남은 TTL 조회 (초 단위)"""
        redis_key = f"{self.prefix}{key}"
        return self.redis_client.ttl(redis_key)
    
    def exists(self, key: str) -> bool:
        """Challenge 존재 여부 확인"""
        redis_key = f"{self.prefix}{key}"
        return self.redis_client.exists(redis_key) > 0

# Challenge 관리자 인스턴스 (바이너리 Redis 클라이언트 사용)
challenge_manager = ChallengeManager(redis_manager.redis_client_binary)

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_ID,
        cursor_factory=RealDictCursor,
        sslmode='verify-full',
        sslrootcert=DB_ROOT_CA_PATH,
        sslcert=DB_CERT_PATH,       
        sslkey=DB_CERT_KEY_PATH,
    )

# ==================== Pydantic 모델 ====================

class PasskeyRegisterBeginRequest(BaseModel):
    """Passkey 등록 시작 요청"""
    username: str

class PasskeyRegisterCompleteRequest(BaseModel):
    """Passkey 등록 완료 요청"""
    username: str
    attestationResponse: Any  # dict 대신 Any 사용하여 bytes 데이터 허용

class PasskeyLoginBeginRequest(BaseModel):
    """Passkey 로그인 시작 요청"""
    username: str

class PasskeyLoginCompleteRequest(BaseModel):
    """Passkey 로그인 완료 요청"""
    username: str
    assertionResponse: Any  # dict 대신 Any 사용하여 bytes 데이터 허용

class TokenResponse(BaseModel):
    """토큰 응답 모델"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """토큰 갱신 요청 모델"""
    refresh_token: str


class SessionInfo(BaseModel):
    """세션 정보 모델"""
    ip: str
    user_agent: str
    created_at: str


class UserResponse(BaseModel):
    """사용자 정보 응답 모델"""
    user_id: int
    username: str


# ==================== Passkey 엔드포인트 ====================

@router.post("/passkey/register/begin")
async def passkey_register_begin(req: PasskeyRegisterBeginRequest):
    """
    Passkey 등록 시작
    
    1. 사용자 존재 여부 확인
    2. WebAuthn registration options 생성
    3. Challenge 저장
    """
    username = req.username
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사용자 존재 여부 확인
        cursor.execute(
            "SELECT user_id FROM users WHERE username = %s",
            (username,)
        )
        existing_user = cursor.fetchone()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # WebAuthn options 생성
        options = generate_registration_options(
            rp_id=RP_ID,
            rp_name=RP_NAME,
            user_id=username.encode("utf-8"),
            user_name=username,
            user_display_name=username,
            authenticator_selection=AuthenticatorSelectionCriteria(
                user_verification=UserVerificationRequirement.PREFERRED,
            ),
            supported_pub_key_algs=[
                COSEAlgorithmIdentifier.ECDSA_SHA_256,
                COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
            ],
        )
        
        # Challenge 저장 (Redis 사용)
        challenge_manager.save_challenge(username, options.challenge)
        
        print(f"📝 Registration started for: {username}")
        
        return json.loads(options_to_json(options))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Register begin error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if 'conn' in locals():
            conn.close()


@router.post("/passkey/register/complete")
async def passkey_register_complete(req: PasskeyRegisterCompleteRequest):
    """
    Passkey 등록 완료
    
    1. WebAuthn response 검증
    2. 사용자 생성 (DB에 저장)
    3. Credential 저장
    """
    username = req.username
    attestation_response = req.attestationResponse
    
    try:
        # Challenge 조회 (Redis에서)
        expected_challenge = challenge_manager.get_challenge(username)
        if not expected_challenge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Challenge not found. Please restart registration."
            )
        
        # WebAuthn response 검증
        verification = verify_registration_response(
            credential=attestation_response,
            expected_challenge=expected_challenge,
            expected_origin=RP_ORIGIN,
            expected_rp_id=RP_ID,
        )
        
        # DB에 사용자 및 Credential 저장
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사용자 생성
        cursor.execute(
            """
            INSERT INTO users (username, created_at, last_login)
            VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING user_id
            """,
            (username,)
        )
        user_id = cursor.fetchone()['user_id']
        
        # Credential 저장
        cursor.execute(
            """
            INSERT INTO passkey_credentials (
                user_id,
                credential_id,
                public_key,
                sign_count,
                created_at
            ) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (
                user_id,
                base64.b64encode(verification.credential_id).decode('utf-8'),
                base64.b64encode(verification.credential_public_key).decode('utf-8'),
                verification.sign_count,
            )
        )
        
        conn.commit()
        
        # Challenge 삭제 (Redis에서)
        challenge_manager.delete_challenge(username)
        
        print(f"✅ Registration successful for: {username} (user_id={user_id})")
        
        return {"verified": True, "message": "Registration successful"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Register complete error: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        if 'conn' in locals():
            conn.close()


@router.post("/passkey/login/begin")
async def passkey_login_begin(req: PasskeyLoginBeginRequest):
    """
    Passkey 로그인 시작
    
    1. 사용자 조회
    2. 저장된 Credential 조회
    3. WebAuthn authentication options 생성
    """
    username = req.username
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사용자 조회
        cursor.execute(
            "SELECT user_id FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = user['user_id']
        
        # 저장된 Credential 조회
        cursor.execute(
            """
            SELECT credential_id, public_key
            FROM passkey_credentials
            WHERE user_id = %s
            """,
            (user_id,)
        )
        credentials = cursor.fetchall()
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No passkey found for this user"
            )
        
        # Credential descriptors 생성
        allow_credentials = [
            PublicKeyCredentialDescriptor(
                id=base64.b64decode(cred['credential_id']),
                transports=[AuthenticatorTransport.INTERNAL, AuthenticatorTransport.HYBRID],
            )
            for cred in credentials
        ]
        
        # WebAuthn options 생성
        options = generate_authentication_options(
            rp_id=RP_ID,
            allow_credentials=allow_credentials,
            user_verification=UserVerificationRequirement.PREFERRED,
        )
        
        # Challenge 저장 (Redis 사용)
        challenge_manager.save_challenge(username, options.challenge)
        
        print(f"🔐 Login started for: {username}")
        
        return json.loads(options_to_json(options))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login begin error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if 'conn' in locals():
            conn.close()


@router.post("/passkey/login/complete", response_model=TokenResponse)
async def passkey_login_complete(request: Request):
    """
    Passkey 로그인 완료
    
    1. WebAuthn response 검증
    2. JWT 토큰 생성
    3. 세션 저장
    """
    try:
        # JSON 본문을 수동으로 파싱 (Pydantic의 자동 파싱 우회)
        body = await request.json()
        username = body.get('username')
        assertion_response = body.get('assertionResponse')
        
        if not username or not assertion_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing username or assertionResponse"
            )
        
        print(f"✅ Request parsed - username type: {type(username)}, assertion_response type: {type(assertion_response)}")
        
        # username이 bytes인 경우 문자열로 변환
        if isinstance(username, bytes):
            username = username.decode('utf-8')
        
        print(f"✅ Username: {username}")
        
        # Challenge 조회 (Redis에서)
        print(f"🔍 Getting challenge for: {username}")
        expected_challenge = challenge_manager.get_challenge(username)
        print(f"✅ Challenge retrieved")
        if not expected_challenge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Challenge not found. Please restart login."
            )
        
        print(f"✅ Challenge retrieved (length: {len(expected_challenge)})")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사용자 조회
        cursor.execute(
            "SELECT user_id FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = user['user_id']
        print(f"✅ User found: {user_id}")
        
        # Credential 조회
        # 'id' 필드만 사용 (Base64URL 문자열)
        credential_id_raw = assertion_response.get('id')
        
        if not credential_id_raw:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credential ID not found in response"
            )
        
        if not isinstance(credential_id_raw, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid credential ID type: {type(credential_id_raw)}"
            )
        
        # Base64URL 문자열을 bytes로 디코딩 후 표준 Base64로 인코딩
        try:
            # Base64URL 디코딩 (패딩 추가)
            credential_id_padded = credential_id_raw + '=' * (4 - len(credential_id_raw) % 4)
            credential_id_bytes = base64.urlsafe_b64decode(credential_id_padded)
            
            # 표준 Base64로 인코딩 (DB 저장 형식과 일치)
            credential_id = base64.b64encode(credential_id_bytes).decode('utf-8')
            print(f"✅ Credential ID converted (length: {len(credential_id_bytes)})")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid credential ID format: {str(e)}"
            )

        cursor.execute(
            """
            SELECT credential_id, public_key, sign_count
            FROM passkey_credentials
            WHERE user_id = %s AND credential_id = %s
            """,
            (user_id, credential_id)
        )
        credential = cursor.fetchone()
        
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )
        
        print(f"✅ Credential found in DB")
        
        # WebAuthn response 검증
        print(f"🔐 Verifying authentication response...")
        try:
            verification = verify_authentication_response(
                credential=assertion_response,
                expected_challenge=expected_challenge,
                expected_origin=RP_ORIGIN,
                expected_rp_id=RP_ID,
                credential_public_key=base64.b64decode(credential['public_key']),
                credential_current_sign_count=credential['sign_count'],
            )
            print(f"✅ Authentication verified successfully")
        except Exception as verify_error:
            print(f"❌ Verification failed: {verify_error}")
            raise
        
        # Sign count 및 last_used 업데이트
        cursor.execute(
            """
            UPDATE passkey_credentials
            SET sign_count = %s, last_used = CURRENT_TIMESTAMP
            WHERE user_id = %s AND credential_id = %s
            """,
            (verification.new_sign_count, user_id, credential_id)
        )
        
        # 마지막 로그인 시간 업데이트
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s",
            (user_id,)
        )
        
        conn.commit()
        
        # Challenge 삭제 (Redis에서)
        challenge_manager.delete_challenge(username)
        
        # JWT 토큰 생성
        token_data = {"user_id": user_id, "username": username}
        access_token = session_manager.create_access_token(token_data)
        refresh_token = session_manager.create_refresh_token(token_data)
        
        # 세션 저장
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        session_manager.save_session(
            user_id=user_id,
            token=access_token,
            ip=client_ip,
            user_agent=user_agent,
            metadata={"username": username, "login_method": "passkey"}
        )
        
        print(f"✅ Login successful for: {username} (user_id={user_id})")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login complete error: {type(e).__name__}")
        print(f"   Error details: {repr(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{type(e).__name__}: {str(e)}"
        )
    finally:
        if 'conn' in locals():
            conn.close()


# ==================== 추가 Passkey 등록 엔드포인트 ====================


@router.post("/passkey/add/begin")
async def passkey_add_begin(req: PasskeyRegisterBeginRequest, current_user: dict = Depends(get_current_user)):
    """
    기존 사용자에게 추가 Passkey 등록 시작 (인증 필요)
    
    1. 이미 로그인된 사용자만 가능
    2. WebAuthn registration options 생성
    3. Challenge 저장
    """
    username = req.username
    user_id = current_user.get("user_id")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사용자 확인
        cursor.execute(
            "SELECT user_id, username FROM users WHERE user_id = %s",
            (user_id,)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Username 일치 확인 (본인만 추가 가능)
        if user['username'] != username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only add passkeys to your own account"
            )
        
        # 기존 Credential 개수 확인 (선택적 제한)
        cursor.execute(
            "SELECT COUNT(*) as count FROM passkey_credentials WHERE user_id = %s",
            (user_id,)
        )
        credential_count = cursor.fetchone()['count']
        
        if credential_count >= 10:  # 최대 10개 제한
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum number of passkeys reached (10)"
            )
        
        # WebAuthn options 생성
        options = generate_registration_options(
            rp_id=RP_ID,
            rp_name=RP_NAME,
            user_id=str(user_id).encode("utf-8"),
            user_name=username,
            user_display_name=username,
            authenticator_selection=AuthenticatorSelectionCriteria(
                user_verification=UserVerificationRequirement.PREFERRED,
            ),
            supported_pub_key_algs=[
                COSEAlgorithmIdentifier.ECDSA_SHA_256,
                COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
            ],
        )
        
        # Challenge 저장 (user_id를 키로 사용, Redis 사용)
        challenge_manager.save_challenge(f"add_{user_id}", options.challenge)
        
        print(f"📝 Additional passkey registration started for: {username} (user_id={user_id})")
        
        return json.loads(options_to_json(options))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Add passkey begin error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if 'conn' in locals():
            conn.close()


@router.post("/passkey/add/complete")
async def passkey_add_complete(req: PasskeyRegisterCompleteRequest, current_user: dict = Depends(get_current_user)):
    """
    추가 Passkey 등록 완료 (인증 필요)
    
    1. WebAuthn response 검증
    2. 새 Credential 저장
    """
    username = req.username
    attestation_response = req.attestationResponse
    user_id = current_user.get("user_id")
    
    try:
        # Challenge 조회 (Redis에서)
        challenge_key = f"add_{user_id}"
        expected_challenge = challenge_manager.get_challenge(challenge_key)
        if not expected_challenge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Challenge not found. Please restart registration."
            )
        
        # WebAuthn response 검증
        verification = verify_registration_response(
            credential=attestation_response,
            expected_challenge=expected_challenge,
            expected_origin=RP_ORIGIN,
            expected_rp_id=RP_ID,
        )
        
        # DB에 Credential 저장
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사용자 확인
        cursor.execute(
            "SELECT username FROM users WHERE user_id = %s",
            (user_id,)
        )
        user = cursor.fetchone()
        
        if not user or user['username'] != username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized"
            )
        
        # Credential 중복 확인
        credential_id_b64 = base64.b64encode(verification.credential_id).decode('utf-8')
        cursor.execute(
            "SELECT credential_id FROM passkey_credentials WHERE credential_id = %s",
            (credential_id_b64,)
        )
        existing_cred = cursor.fetchone()
        
        if existing_cred:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This passkey is already registered"
            )
        
        # 새 Credential 저장
        cursor.execute(
            """
            INSERT INTO passkey_credentials (
                user_id,
                credential_id,
                public_key,
                sign_count,
                created_at
            ) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (
                user_id,
                credential_id_b64,
                base64.b64encode(verification.credential_public_key).decode('utf-8'),
                verification.sign_count,
            )
        )
        
        conn.commit()
        
        # Challenge 삭제 (Redis에서)
        challenge_manager.delete_challenge(challenge_key)
        
        print(f"✅ Additional passkey added for: {username} (user_id={user_id})")
        
        return {"verified": True, "message": "Passkey added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Add passkey complete error: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        if 'conn' in locals():
            conn.close()


@router.get("/passkey/list")
async def passkey_list(current_user: dict = Depends(get_current_user)):
    """
    현재 사용자의 등록된 Passkey 목록 조회
    
    Returns:
        Passkey 목록 (credential_id, created_at, last_used)
    """
    user_id = current_user.get("user_id")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT 
                credential_id,
                created_at,
                last_used,
                sign_count
            FROM passkey_credentials
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        credentials = cursor.fetchall()
        
        return {
            "passkeys": [
                {
                    "credential_id": cred['credential_id'][:20] + "...",  # 일부만 표시
                    "created_at": cred['created_at'].isoformat() if cred['created_at'] else None,
                    "last_used": cred['last_used'].isoformat() if cred['last_used'] else None,
                    "sign_count": cred['sign_count']
                }
                for cred in credentials
            ],
            "total": len(credentials)
        }
        
    except Exception as e:
        print(f"❌ List passkeys error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if 'conn' in locals():
            conn.close()


@router.delete("/passkey/remove/{credential_id}")
async def passkey_remove(credential_id: str, current_user: dict = Depends(get_current_user)):
    """
    Passkey 삭제
    
    Args:
        credential_id: 삭제할 Credential ID (일부만 전달 가능)
    
    Returns:
        성공 메시지
    """
    user_id = current_user.get("user_id")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 최소 1개는 남겨야 함
        cursor.execute(
            "SELECT COUNT(*) as count FROM passkey_credentials WHERE user_id = %s",
            (user_id,)
        )
        count = cursor.fetchone()['count']
        
        if count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove last passkey. At least one passkey must remain."
            )
        
        # Credential 삭제 (LIKE를 사용하여 일부 일치도 허용)
        cursor.execute(
            """
            DELETE FROM passkey_credentials
            WHERE user_id = %s AND credential_id LIKE %s
            RETURNING credential_id
            """,
            (user_id, f"{credential_id}%")
        )
        deleted = cursor.fetchone()
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Passkey not found"
            )
        
        conn.commit()
        
        print(f"🗑️ Passkey removed for user_id={user_id}")
        
        return {"message": "Passkey removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Remove passkey error: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if 'conn' in locals():
            conn.close()


# ==================== 세션 관리 엔드포인트 ====================


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    로그아웃 (현재 세션만)
    
    Args:
        current_user: 현재 인증된 사용자
    
    Returns:
        성공 메시지
    """
    token = current_user.get("token")
    user_id = current_user.get("user_id")
    jti = current_user.get("jti")
    
    # JWT를 블랙리스트에 추가
    exp_timestamp = current_user.get("session", {}).get("created_at")
    if exp_timestamp:
        exp = datetime.fromisoformat(exp_timestamp) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        session_manager.blacklist_token(jti, exp)
    
    # 세션 삭제
    session_manager.delete_session(token, user_id)
    
    return {"message": "Logged out successfully"}


@router.post("/logout-all")
async def logout_all_devices(current_user: dict = Depends(get_current_user)):
    """
    모든 디바이스에서 로그아웃
    
    Args:
        current_user: 현재 인증된 사용자
    
    Returns:
        무효화된 세션 개수
    """
    user_id = current_user.get("user_id")
    
    # 모든 세션 무효화
    count = session_manager.revoke_all_user_sessions(user_id)
    
    return {
        "message": f"All sessions revoked successfully",
        "sessions_revoked": count
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, refresh_data: RefreshRequest):
    """
    Access Token 갱신
    
    Args:
        request: FastAPI Request 객체
        refresh_data: Refresh Token
    
    Returns:
        새로운 Access Token 및 Refresh Token
    """
    # Refresh Token 검증
    payload = session_manager.verify_token(refresh_data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("user_id")
    username = payload.get("username")
    
    # 새로운 토큰 생성
    token_data = {"user_id": user_id, "username": username}
    new_access_token = session_manager.create_access_token(token_data)
    new_refresh_token = session_manager.create_refresh_token(token_data)
    
    # 새 세션 저장
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    session_manager.save_session(
        user_id=user_id,
        token=new_access_token,
        ip=client_ip,
        user_agent=user_agent,
        metadata={"username": username, "login_method": "refresh"}
    )
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    현재 사용자 정보 조회
    
    Args:
        current_user: 현재 인증된 사용자
    
    Returns:
        사용자 정보
    """
    return UserResponse(
        user_id=current_user.get("user_id"),
        username=current_user.get("session", {}).get("username", "")
    )


@router.get("/sessions", response_model=List[SessionInfo])
async def get_active_sessions(current_user: dict = Depends(get_current_user)):
    """
    현재 사용자의 활성 세션 목록
    
    Args:
        current_user: 현재 인증된 사용자
    
    Returns:
        활성 세션 리스트
    """
    user_id = current_user.get("user_id")
    sessions = session_manager.get_user_active_sessions(user_id)
    
    return [
        SessionInfo(
            ip=session.get("ip", "unknown"),
            user_agent=session.get("user_agent", ""),
            created_at=session.get("created_at", "")
        )
        for session in sessions
    ]


@router.get("/health")
async def health_check():
    """
    인증 시스템 헬스 체크 (Redis 연결 확인)
    
    Returns:
        시스템 상태
    """
    try:
        session_manager.redis_client.ping()
        return {
            "status": "healthy",
            "redis": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "redis": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
