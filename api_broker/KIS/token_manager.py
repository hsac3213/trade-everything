from ..Common.RedisManager import redis_manager
from .constants import *
from ..Common.DBManager import get_db_conn

import json
import requests

def get_key(user_id):
    key = f"{user_id}_KIS_KEY"

    # 캐시된 키가 유효한지 검사
    if redis_manager.redis_client.exists(key) > 0:
        #print("Use cached access key.")
        return json.loads(redis_manager.redis_client.get(name=key))

    with get_db_conn() as conn:
        cursor = conn.cursor()

        app_key = ""
        sec_key = ""

        account_number_0 = ""
        account_number_1 = ""

        hts_id = ""
        
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

        cursor.execute(
            "SELECT token FROM user_tokens WHERE user_id = %s and broker_name = 'KIS' and token_name = %s",
            (user_id, "ACCOUNT_NUMBER_0",)
        )
        token = cursor.fetchone()
        if token != None:
            account_number_0 = token["token"]

        cursor.execute(
            "SELECT token FROM user_tokens WHERE user_id = %s and broker_name = 'KIS' and token_name = %s",
            (user_id, "ACCOUNT_NUMBER_1",)
        )
        token = cursor.fetchone()
        if token != None:
            account_number_1 = token["token"]

        cursor.execute(
            "SELECT token FROM user_tokens WHERE user_id = %s and broker_name = 'KIS' and token_name = %s",
            (user_id, "HTS_ID",)
        )
        token = cursor.fetchone()
        if token != None:
            hts_id = token["token"]

        conn.close()

        key_dict = {
            "app_key": app_key,
            "sec_key" : sec_key,
            "account_number_0": account_number_0,
            "account_number_1": account_number_1,
            "hts_id": hts_id,
        }
        #pprint(key_dict)

        redis_manager.redis_client.set(name=key, value=json.dumps(key_dict), ex=60 * 60 * 1)

        return key_dict
    

def get_access_token(user_id):
    key = f"{user_id}_KIS_Token"

    # 캐시된 토큰이 유효한지 검사
    if redis_manager.redis_client.exists(key) > 0:
        #print("Use cached access token.")
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

        # KIS API 서버에 새로운 토큰을 요청
        print('Current access token in cache is expired. Request new access token.')
        json_req = {
            'grant_type': 'client_credentials',
            'appkey': app_key,
            'appsecret': sec_key,
        }
        headers = { 'content-type': 'application/json' }
        resp = requests.post(API_URL + '/oauth2/tokenP', headers=headers, data=json.dumps(json_req))

        if 'access_token' in resp.json():
            access_token = resp.json()['access_token']
            redis_manager.redis_client.set(name=key, value=access_token, ex=60 * 60 * 23)
        
            return access_token
        
        return None