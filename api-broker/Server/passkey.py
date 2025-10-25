import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import webauthn
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor,
)
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime, timedelta
import base64

# --- FastAPI 앱 설정 ---
app = FastAPI()

# --- CORS 설정 ---
origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebAuthn 설정 ---
RP_ID = "localhost"
RP_NAME = "My Python App"
RP_ORIGIN = "http://localhost:5173"

# --- MariaDB 연결 ---
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    webauthn_user_id = Column(LargeBinary(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    credentials = relationship("Credential", back_populates="user", cascade="all, delete-orphan")

class Credential(Base):
    __tablename__ = 'credentials'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    credential_id = Column(LargeBinary(1024), unique=True, nullable=False)
    public_key = Column(LargeBinary, nullable=False)
    sign_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="credentials")

class Challenge(Base):
    __tablename__ = 'challenges'
    username = Column(String(255), primary_key=True)
    challenge = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)

# MariaDB 연결 문자열 수정 필요
engine = create_engine('mysql+pymysql://tradeuser:trade2025!@localhost:3306/tradedb')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# --- Pydantic 모델 ---
class UserRequest(BaseModel):
    username: str

# --- API 엔드포인트 ---
@app.post("/register/begin")
def register_begin(req: UserRequest):
    username = req.username
    session = Session()
    
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            user_id = f"user_{username}_id".encode("utf-8")
            user = User(username=username, webauthn_user_id=user_id)
            session.add(user)
            session.commit()
        else:
            user_id = user.webauthn_user_id
        
        auth_selection = AuthenticatorSelectionCriteria(
            authenticator_attachment=None,
            resident_key=None,
            user_verification=UserVerificationRequirement.PREFERRED,
        )
        
        options = webauthn.generate_registration_options(
            rp_id=RP_ID,
            rp_name=RP_NAME,
            user_id=user_id,
            user_name=username,
            user_display_name=username,
            authenticator_selection=auth_selection,
        )
        
        # 챌린지 저장 (bytes를 base64 문자열로 변환)
        challenge_str = base64.b64encode(options.challenge).decode('utf-8')
        
        challenge_obj = session.query(Challenge).filter_by(username=username).first()
        if challenge_obj:
            challenge_obj.challenge = challenge_str
            challenge_obj.expires_at = datetime.utcnow() + timedelta(seconds=60)
        else:
            challenge_obj = Challenge(
                username=username,
                challenge=challenge_str,
                expires_at=datetime.utcnow() + timedelta(seconds=60)
            )
            session.add(challenge_obj)
        session.commit()
        
        return webauthn.helpers.options_to_json(options)
        
    finally:
        session.close()

@app.post("/register/complete")
async def register_complete(req: dict):
    username = req.get("username")
    attestation_response = req.get("attestationResponse")
    session = Session()
    
    try:
        user = session.query(User).filter_by(username=username).first()
        challenge_obj = session.query(Challenge).filter_by(username=username).first()
        
        if not user or not challenge_obj:
            raise HTTPException(status_code=404, detail="User or challenge not found")
        
        # challenge를 base64 디코딩하여 bytes로 변환
        expected_challenge = base64.b64decode(challenge_obj.challenge)
        
        verification = webauthn.verify_registration_response(
            credential=attestation_response,
            expected_challenge=expected_challenge,
            expected_origin=RP_ORIGIN,
            expected_rp_id=RP_ID,
        )
        
        # 크리덴셜 저장
        credential = Credential(
            user_id=user.id,
            credential_id=verification.credential_id,
            public_key=verification.credential_public_key,
            sign_count=0
        )
        session.add(credential)
        session.delete(challenge_obj)
        session.commit()
        
        print(f"✅ Registration successful for user: {username}")
        return {"verified": True}
        
    except Exception as e:
        session.rollback()
        print(f"❌ Registration Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

@app.post("/login/begin")
def login_begin(req: UserRequest):
    username = req.username
    session = Session()
    
    try:
        user = session.query(User).filter_by(username=username).first()
        
        if not user or not user.credentials:
            raise HTTPException(status_code=404, detail="User not found or no credentials registered")
        
        # 등록된 크리덴셜을 PublicKeyCredentialDescriptor 객체로 변환
        allowed_credentials = []
        for cred in user.credentials:
            allowed_credentials.append(
                PublicKeyCredentialDescriptor(id=cred.credential_id)
            )
        
        options = webauthn.generate_authentication_options(
            rp_id=RP_ID,
            allow_credentials=allowed_credentials,
            user_verification=UserVerificationRequirement.PREFERRED,
        )
        
        # 챌린지 저장 (bytes를 base64 문자열로 변환)
        challenge_str = base64.b64encode(options.challenge).decode('utf-8')
        
        challenge_obj = session.query(Challenge).filter_by(username=username).first()
        if challenge_obj:
            challenge_obj.challenge = challenge_str
            challenge_obj.expires_at = datetime.utcnow() + timedelta(seconds=60)
        else:
            challenge_obj = Challenge(
                username=username,
                challenge=challenge_str,
                expires_at=datetime.utcnow() + timedelta(seconds=60)
            )
            session.add(challenge_obj)
        session.commit()
        
        options_json = webauthn.helpers.options_to_json(options)
        print(f"Sending authentication options to client")
        return options_json
        
    finally:
        session.close()

@app.post("/login/complete")
async def login_complete(req: dict):
    username = req.get("username")
    assertion_response = req.get("assertionResponse")
    session = Session()
    
    try:
        user = session.query(User).filter_by(username=username).first()
        challenge_obj = session.query(Challenge).filter_by(username=username).first()
        
        if not user or not challenge_obj:
            raise HTTPException(status_code=404, detail="User or challenge not found")
        
        # DB에서 일치하는 크리덴셜 찾기
        credential_id = assertion_response.get("id") or assertion_response.get("rawId")
        
        matching_cred = None
        for cred in user.credentials:
            # credential_id는 base64url 문자열로 올 수 있으므로 여러 방식으로 비교
            if cred.credential_id == credential_id:
                matching_cred = cred
                break
            elif isinstance(credential_id, str) and cred.credential_id == credential_id.encode():
                matching_cred = cred
                break
            elif isinstance(cred.credential_id, bytes) and isinstance(credential_id, str):
                # base64url 디코딩 비교
                try:
                    decoded_id = base64.urlsafe_b64decode(credential_id + '==')  # padding 추가
                    if cred.credential_id == decoded_id:
                        matching_cred = cred
                        break
                except:
                    pass
        
        if not matching_cred:
            raise HTTPException(status_code=404, detail="Credential not registered for this user")
        
        # challenge를 base64 디코딩하여 bytes로 변환
        expected_challenge = base64.b64decode(challenge_obj.challenge)
        
        # webauthn 라이브러리에 딕셔너리로 전달
        verification = webauthn.verify_authentication_response(
            credential=assertion_response,
            expected_challenge=expected_challenge,
            expected_origin=RP_ORIGIN,
            expected_rp_id=RP_ID,
            credential_public_key=matching_cred.public_key,
            credential_current_sign_count=matching_cred.sign_count,
        )
        
        # 검증 성공 시 (예외가 발생하지 않으면 성공)
        # !! 중요: 카운터 업데이트 (재전송 공격 방지)
        matching_cred.sign_count = verification.new_sign_count
        session.delete(challenge_obj)  # 사용한 챌린지 삭제
        session.commit()
        
        print(f"✅ Authentication successful for user: {username}")
        # (실제 앱) 여기서 JWT 토큰 등 세션 발급
        return {"verified": True, "message": "Login successful!"}
        
    except Exception as e:
        session.rollback()
        print(f"❌ Authentication Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Verification failed: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)