from .user_settings import UserSettingsManager
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/favorites", tags=["favorites"])

class AddFavoriteRequest(BaseModel):
    broker: str
    symbol: str
    display_name: Optional[str] = None

class FavoriteSymbol(BaseModel):
    broker: str
    symbol: str
    display_name: Optional[str]
    added_at: str

# 사용자 인증 (실제 구현 시 JWT 사용)
async def get_current_user_id() -> int:
    # JWT 토큰에서 user_id 추출
    return 1  # 예시

db = UserSettingsManager()

@router.on_event("startup")
async def startup():
    await db.connect()

@router.on_event("shutdown")
async def shutdown():
    await db.close()

@router.post("/add")
async def add_favorite(
    request: AddFavoriteRequest,
    user_id: int = Depends(get_current_user_id)
):
    """즐겨찾기 추가"""
    success = await db.add_favorite_symbol(
        user_id,
        request.broker,
        request.symbol,
        request.display_name
    )
    
    if success:
        return {"message": "Added to favorites", "success": True}
    else:
        return {"message": "Already in favorites", "success": False}

@router.delete("/remove")
async def remove_favorite(
    broker: str,
    symbol: str,
    user_id: int = Depends(get_current_user_id)
):
    """즐겨찾기 제거"""
    success = await db.remove_favorite_symbol(user_id, broker, symbol)
    
    if success:
        return {"message": "Removed from favorites", "success": True}
    else:
        raise HTTPException(status_code=404, detail="Not found in favorites")

@router.get("/list", response_model=List[FavoriteSymbol])
async def get_favorites(
    broker: Optional[str] = None,
    user_id: int = Depends(get_current_user_id)
):
    """즐겨찾기 목록 조회"""
    favorites = await db.get_favorite_symbols(user_id, broker)
    return favorites

@router.get("/check")
async def check_favorite(
    broker: str,
    symbol: str,
    user_id: int = Depends(get_current_user_id)
):
    """즐겨찾기 여부 확인"""
    is_fav = await db.is_favorite_symbol(user_id, broker, symbol)
    return {"is_favorite": is_fav}