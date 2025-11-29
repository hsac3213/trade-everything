from .user_settings import UserSettingsManager
from .auth_dependency import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import traceback

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

# DB 매니저 생성 함수
def get_db():
    db = UserSettingsManager()
    try:
        yield db
    except Exception as e:
        print(f"❌ DB Connection Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
    finally:
        pass

@router.post("/add")
async def add_favorite(
    request: AddFavoriteRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: UserSettingsManager = Depends(get_db)
):
    user_id = current_user["user_id"]
    
    success = db.add_favorite_symbol(
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
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: UserSettingsManager = Depends(get_db)
):
    user_id = current_user["user_id"]
    
    success = db.remove_favorite_symbol(user_id, broker, symbol)
    
    if success:
        return {"message": "Removed from favorites", "success": True}
    else:
        raise HTTPException(status_code=404, detail="Not found in favorites")

@router.get("/list", response_model=List[FavoriteSymbol])
async def get_favorites(
    broker: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: UserSettingsManager = Depends(get_db)
):
    user_id = current_user["user_id"]
    
    favorites = db.get_favorite_symbols(user_id, broker)
    return favorites

