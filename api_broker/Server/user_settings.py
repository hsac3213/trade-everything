from ..Common.DBManager import get_db_conn
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from typing import List, Dict, Optional
from datetime import datetime

class UserSettingsManager:
    def __init__(self):
        self.conn = None
    
    def connect(self):
        self.conn = get_db_conn()
    
    def get_connection(self):
        if self.conn is None or self.conn.closed:
            self.connect()
        return self.conn
    
    # 즐겨찾기 관리

    def add_favorite_symbol(self, user_id: int, broker: str, symbol: str, display_name: Optional[str] = None) -> bool:
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT setting_data FROM user_settings
                    WHERE user_id = %s AND setting_type = 'favorites'
                """, (user_id,))
                
                row = cursor.fetchone()
                
                if row:
                    favorites = row['setting_data']
                    
                    # 중복 검사
                    for fav in favorites:
                        if fav['broker'] == broker and fav['symbol'] == symbol:
                            return False
                    
                    # 새 항목 추가
                    favorites.append({
                        'broker': broker,
                        'symbol': symbol,
                        'display_name': display_name,
                        'added_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    # 업데이트
                    cursor.execute("""
                        UPDATE user_settings
                        SET setting_data = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s AND setting_type = 'favorites'
                    """, (json.dumps(favorites), user_id))
                else:
                    # 새로 생성
                    favorites = [{
                        'broker': broker,
                        'symbol': symbol,
                        'display_name': display_name,
                        'added_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }]
                    
                    cursor.execute("""
                        INSERT INTO user_settings (user_id, setting_type, setting_data)
                        VALUES (%s, 'favorites', %s)
                    """, (user_id, json.dumps(favorites)))
                
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            print(f"Error adding favorite: {e}")
            return False
    
    def remove_favorite_symbol(self, user_id: int, broker: str, symbol: str) -> bool:
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                # 기존 즐겨찾기 조회
                cursor.execute("""
                    SELECT setting_data FROM user_settings
                    WHERE user_id = %s AND setting_type = 'favorites'
                """, (user_id,))
                
                row = cursor.fetchone()
                
                if not row:
                    return False
                
                favorites = row['setting_data']
                
                # 해당 항목 제거
                new_favorites = [
                    fav for fav in favorites
                    if not (fav['broker'] == broker and fav['symbol'] == symbol)
                ]
                
                if len(new_favorites) == len(favorites):
                    return False  # 제거할 항목 없음
                
                # 업데이트
                cursor.execute("""
                    UPDATE user_settings
                    SET setting_data = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND setting_type = 'favorites'
                """, (json.dumps(new_favorites), user_id))
                
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            print(f"Error removing favorite: {e}")
            return False
    
    def get_favorite_symbols(self, user_id: int, broker: Optional[str] = None) -> List[Dict]:
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT setting_data FROM user_settings
                    WHERE user_id = %s AND setting_type = 'favorites'
                """, (user_id,))
                
                row = cursor.fetchone()
                
                if not row:
                    return []
                
                favorites = row['setting_data']
                
                # broker 필터링
                if broker:
                    favorites = [fav for fav in favorites if fav['broker'] == broker]
                
                return favorites
        except Exception as e:
            print(f"Error getting favorites: {e}")
            return []
    
    # 기타 설정 관련 메서드
    
    def get_setting(self, user_id: int, setting_type: str) -> Optional[Dict]:
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT setting_data FROM user_settings
                    WHERE user_id = %s AND setting_type = %s
                """, (user_id, setting_type))
                
                row = cursor.fetchone()
                return row['setting_data'] if row else None
        except Exception as e:
            print(f"Error getting setting: {e}")
            return None
    
    def update_setting(self, user_id: int, setting_type: str, setting_data: Dict) -> bool:
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_settings (user_id, setting_type, setting_data)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, setting_type) 
                    DO UPDATE SET 
                        setting_data = EXCLUDED.setting_data,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, setting_type, json.dumps(setting_data)))
                
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            print(f"Error updating setting: {e}")
            return False
    
    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()