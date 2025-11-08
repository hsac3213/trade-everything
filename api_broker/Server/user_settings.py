from .db_manager import *
import asyncpg
import json
from typing import List, Dict, Optional
from datetime import datetime

class UserSettingsManager:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_ID,
            cursor_factory=RealDictCursor,
            sslmode='verify-full',
            sslrootcert=DB_ROOT_CA_PATH,
            sslcert=DB_CERT_PATH,       
            sslkey=DB_CERT_KEY_PATH,
        )
    
    # 즐겨찾기 관리
    async def add_favorite_symbol(self, user_id: int, broker: str, symbol: str, display_name: Optional[str] = None) -> bool:
        async with self.pool.acquire() as conn:
            try:
                old_favorites = await conn.fetchrow("""
                    SELECT setting_data FROM user_settings
                    WHERE user_id = $1 AND setting_type = 'favorites'
                """, user_id)
                
                if old_favorites:
                    favorites = old_favorites['setting_data']
                    
                    # 중복 검사
                    for fav in favorites:
                        if fav['broker'] == broker and fav['symbol'] == symbol:
                            return False
                    
                    favorites.append({
                        'broker': broker,
                        'symbol': symbol,
                        'display_name': display_name,
                        'added_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    await conn.execute("""
                        UPDATE user_settings
                        SET setting_data = $1, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = $2 AND setting_type = 'favorites'
                    """, json.dumps(favorites), user_id)
                else:
                    favorites = [{
                        'broker': broker,
                        'symbol': symbol,
                        'display_name': display_name,
                        'added_at': datetime.utcnow().isoformat()
                    }]
                    
                    await conn.execute("""
                        INSERT INTO user_settings (user_id, setting_type, setting_data)
                        VALUES ($1, 'favorites', $2)
                    """, user_id, json.dumps(favorites))
                
                return True
            except Exception as e:
                print(f"Error adding favorite: {e}")
                return False
    
    async def remove_favorite_symbol(self, user_id: int, broker: str, symbol: str) -> bool:
        async with self.pool.acquire() as conn:
            try:
                old_favorites = await conn.fetchrow("""
                    SELECT setting_data FROM user_settings
                    WHERE user_id = $1 AND setting_type = 'favorites'
                """, user_id)
                
                if not old_favorites:
                    return False
                
                favorites = old_favorites['setting_data']
                
                new_favorites = [
                    fav for fav in favorites
                    if not (fav['broker'] == broker and fav['symbol'] == symbol)
                ]
                
                if len(new_favorites) == len(favorites):
                    return False
                
                await conn.execute("""
                    UPDATE user_settings
                    SET setting_data = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $2 AND setting_type = 'favorites'
                """, json.dumps(new_favorites), user_id)
                
                return True
            except Exception as e:
                print(f"Error removing favorite: {e}")
                return False
    
    async def get_favorite_symbols(self, user_id: int, broker: Optional[str] = None) -> List[Dict]:
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow("""
                    SELECT setting_data FROM user_settings
                    WHERE user_id = $1 AND setting_type = 'favorites'
                """, user_id)
                
                if not row:
                    return []
                
                favorites = row['setting_data']
                
                if broker:
                    favorites = [fav for fav in favorites if fav['broker'] == broker]
                
                return favorites
            except Exception as e:
                print(f"Error getting favorites: {e}")
                return []
    
    # 기타 설정 관련 메서드
    
    async def get_setting(self, user_id: int, setting_type: str) -> Optional[Dict]:
        """특정 타입의 설정 조회"""
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow("""
                    SELECT setting_data FROM user_settings
                    WHERE user_id = $1 AND setting_type = $2
                """, user_id, setting_type)
                
                return row['setting_data'] if row else None
            except Exception as e:
                print(f"Error getting setting: {e}")
                return None
    
    async def update_setting(self, user_id: int, setting_type: str, setting_data: Dict) -> bool:
        """설정 업데이트 또는 생성"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO user_settings (user_id, setting_type, setting_data)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id, setting_type) 
                    DO UPDATE SET 
                        setting_data = EXCLUDED.setting_data,
                        updated_at = CURRENT_TIMESTAMP
                """, user_id, setting_type, json.dumps(setting_data))
                return True
            except Exception as e:
                print(f"Error updating setting: {e}")
                return False
    
    async def close(self):
        if self.pool:
            await self.pool.close()