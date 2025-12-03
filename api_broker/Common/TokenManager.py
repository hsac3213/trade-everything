from .DBManager import get_db_conn

from typing import List, Dict, Optional

class TokenManager:
    def __init__(self):
        print("[ TokenManager ]")
        print("생성자 호출됨")

    def __del__(self):
        print("[ TokenManager ]")
        print("소멸자 호출됨")
    
    def get_tokens(self, user_id: int, broker: Optional[str] = None) -> List[Dict]:
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM user_tokens
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
                    conn.commit()
                    
                    return row["tokens_data"][broker]
        except Exception as e:
            conn.rollback()
            print("[ TokenManager ]")
            print("Exception:")
            print(e)
            return None