from ..Server.redis_manager import RedisManager
from .constants import *

import psycopg2
from psycopg2.extras import RealDictCursor

import os
import json
import requests

# DB 서버 관련 환경변수 읽기
DB_HOST = os.environ.get("DB_HOST")
DB_ID = os.environ.get("DB_ID")
DB_NAME = "tedb"
DB_ROOT_CA_PATH = os.environ.get("DB_ROOT_CA_PATH")
DB_CERT_PATH = os.environ.get("DB_CERT_PATH")
DB_CERT_KEY_PATH = os.environ.get("DB_CERT_KEY_PATH")

# 환경변수로부터 API 키와 계좌 정보를 가져옴
#APP_KEY = os.environ.get("KIS_APP")
#SEC_KEY = os.environ.get("KIS_SEC")

#ACCOUNT_NUMBER_0 = os.environ.get("ACCOUNT_NUMBER_0")
#ACCOUNT_NUMBER_1 = os.environ.get("ACCOUNT_NUMBER_1")

redis_manager = RedisManager()

def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_ID,
        cursor_factory=RealDictCursor,
        sslmode='verify-full',
        sslrootcert=DB_ROOT_CA_PATH,
        sslcert=DB_CERT_PATH,       
        sslkey=DB_CERT_KEY_PATH,
    )

def get_access_token(user_id):
    key = f"{user_id}_KIS_Token"

    conn = get_db_conn()
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

    # 캐시된 토큰이 유효한지 검사
    if redis_manager.redis_client.exists(key) > 0:
        print("Use cached access token.")
        return redis_manager.redis_client.get(name=key)

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