from ..Common.RedisManager import redis_manager
from .constants import *
from ..Common.DBManager import get_db_conn
from ..Common.Debug import *

import json
import requests

def get_ws_token(user_id):
    key = f"{user_id}_KIS_WS_Token"

    # 캐시된 웹소켓 토큰이 유효한지 검사
    if redis_manager.redis_client.exists(key) > 0:
        Info("Use cached ws token.")
        print(redis_manager.redis_client.get(name=key))
        #print(redis_manager.redis_client.get(name=key))
        return redis_manager.redis_client.get(name=key)

    with get_db_conn() as conn:
        cursor = conn.cursor()

        app_key = ""
        sec_key = ""
        
        cursor.execute(
            "SELECT token FROM user_tokens WHERE user_id = %s and broker_name = 'KIS' and token_name = %s",
            (user_id, "APP",)
        )
        token = cursor.fetchone()
        if token != None:
            app_key = token["token"]

        cursor.execute(
            "SELECT token FROM user_tokens WHERE user_id = %s and broker_name = 'KIS' and token_name = %s",
            (user_id, "SEC",)
        )
        token = cursor.fetchone()
        if token != None:
            sec_key = token["token"]

        conn.close()

        # KIS API 서버에 새로운 웹소켓 토큰을 요청
        print('Current ws token in cache is expired. Request new ws token.')
        json_req = {
            'grant_type': 'client_credentials',
            'appkey': app_key,
            'secretkey': sec_key,
        }
        headers = { 'content-type': 'application/json' }
        resp = requests.post(API_URL + '/oauth2/Approval', headers=headers, data=json.dumps(json_req))

        if 'approval_key' in resp.json():
            approval_key = resp.json()['approval_key']
            redis_manager.redis_client.set(name=key, value=approval_key, ex=60 * 60 * 23)

            return approval_key
        else:
            print('Invalid Response:')
            print(resp.text)
        
        return None