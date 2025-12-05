from .auth_dependency import get_current_user
from ..Common.DBManager import get_db_conn
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

router = APIRouter(prefix="/api/apikeys", tags=["apikeys"])

class APIKeyInfo(BaseModel):
    apikey_name: str
    masked_value: str
    has_value: bool

class APIKeyListResponse(BaseModel):
    broker_name: str
    apikeys: List[APIKeyInfo]

class AddAPIKeyRequest(BaseModel):
    broker_name: str
    apikey_name: str
    apikey: str

class UpdateAPIKeyRequest(BaseModel):
    apikey: str

@router.get("/list", response_model=List[APIKeyListResponse])
async def list_apikeys(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user["user_id"]
    
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT broker_name, token_name, token
                FROM user_tokens
                WHERE user_id = %s
                ORDER BY broker_name, token_name
                """,
                (user_id,)
            )
            
            rows = cursor.fetchall()
            cursor.close()
        
        # 브로커별로 그룹화
        brokers = {}
        for row in rows:
            broker = row["broker_name"]
            if broker not in brokers:
                brokers[broker] = []
            
            # 토큰 마스킹 처리 (앞 4자, 뒤 4자만 표시)
            apikey_value = row["token"]
            if len(apikey_value) > 8:
                masked = "*"
                #masked = apikey_value[:4] + "..." + apikey_value[-4:]
            else:
                masked = "*"
            
            brokers[broker].append({
                "apikey_name": row["token_name"],
                "masked_value": masked,
                "has_value": bool(apikey_value)
            })
        
        # 응답 포맷으로 변환
        result = [
            {
                "broker_name": broker_name,
                "apikeys": apikeys
            }
            for broker_name, apikeys in brokers.items()
        ]
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add")
async def add_apikey(
    request: AddAPIKeyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            
            # UPSERT: 존재하면 업데이트, 없으면 추가
            cursor.execute(
                """
                INSERT INTO user_tokens (user_id, broker_name, token_name, token, updated_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, broker_name, token_name)
                DO UPDATE SET
                    token = EXCLUDED.token,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, request.broker_name, request.apikey_name, request.apikey)
            )
            
            conn.commit()
            cursor.close()
        
        return {"message": "API Key saved successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update/{broker_name}/{apikey_name}")
async def update_apikey(
    broker_name: str,
    apikey_name: str,
    request: UpdateAPIKeyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                UPDATE user_tokens
                SET token = %s, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND broker_name = %s AND token_name = %s
                """,
                (request.apikey, user_id, broker_name, apikey_name)
            )
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Token not found")
            
            conn.commit()
            cursor.close()
        
        return {"message": "API Key updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{broker_name}/{apikey_name}")
async def delete_apikey(
    broker_name: str,
    apikey_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                DELETE FROM user_tokens
                WHERE user_id = %s AND broker_name = %s AND token_name = %s
                """,
                (user_id, broker_name, apikey_name)
            )
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="API Key not found")
            
            conn.commit()
            cursor.close()
        
        return {"message": "API Key deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
