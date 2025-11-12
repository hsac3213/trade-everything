from .DBManager import DBManager

from typing import List, Dict, Optional

class TokenManager:
    def __init__(self):
        print("[ TokenManager ]")
        print("생성자 호출됨")
    
        self.db_manager = DBManager()

    def __del__(self):
        print("[ TokenManager ]")
        print("소멸자 호출됨")

        self.db_manager.close()
    
    def get_tokens(self, user_id: int, broker: Optional[str] = None) -> List[Dict]:
        conn = self.db_manager.get_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT FROM user_tokens
                    WHERE user_id = %s
                """, (user_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                cursor.execute(
                    """
                    UPDATE user_tokens
                    SET last_used = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                    """,
                    (user_id,)
                )
                
                return row["user_tokens"][broker]
        except Exception as e:
            print("[ TokenManager ]")
            print("Exception:")
            print(e)
            return None