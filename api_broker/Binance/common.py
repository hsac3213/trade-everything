from ..Common.RedisManager import redis_manager
from ..Common.Debug import *
from ..Common.DBManager import get_db_conn

import psycopg2
from psycopg2.extras import RealDictCursor

import os
import time
import json
import hmac, hashlib, base64, uuid
from cryptography.hazmat.primitives.serialization import load_pem_private_key

API_URL = "https://api.binance.com"
WSS_URL = "wss://stream.binance.com:9443"
WS_URL = "wss://ws-api.binance.com:443/ws-api/v3"

# 암호화폐 거래 쌍 화이트 리스트
# -> 화이트 리스트 이외의 거래 쌍에 대해서는 모든 요청 거부
CRYPTO_PAIR_WHITELIST = [
    "btcusdt",
    "btcusdc",
    "usdcusdt",
]

def get_key(user_id):
    key = f"{user_id}_Binance_KEY"

    # 캐시된 key가 유효한지 검사
    if redis_manager.redis_client.exists(key) > 0:
        #print("Use cached Binance key.")
        return json.loads(redis_manager.redis_client.get(name=key))

    with get_db_conn() as conn:
        cursor = conn.cursor()

        api_key = ""
        private_key = ""
        
        cursor.execute(
            "SELECT token FROM user_tokens WHERE user_id = %s and broker_name = 'Binance' and token_name = %s",
            (user_id, "API",)
        )
        token = cursor.fetchone()
        if token != None:
            api_key = token["token"]

        cursor.execute(
            "SELECT token FROM user_tokens WHERE user_id = %s and broker_name = 'Binance' and token_name = %s",
            (user_id, "Private",)
        )
        token = cursor.fetchone()
        if token != None:
            private_key = token["token"]

        key_json = {
            "API": api_key,
            "Private": private_key,
        }
        redis_manager.redis_client.set(name=key, value=json.dumps(key_json), ex=60 * 60 * 23)

        Info("")
        return key_json

# https://github.com/binance/binance-signature-examples/tree/master/python
def signing(input):
    """
    signature = hmac.new(SEC_KEY.encode("utf-8"), input.encode("utf-8"), hashlib.sha256)
    signature = signature.hexdigest()
    return signature
    """

# https://developers.binance.com/docs/binance-spot-api-docs/websocket-api/request-security
def get_signed_payload_ws(user_id, method, params):
    private_key_str = get_key(user_id)["Private"]

    private_key_pem = private_key_str.replace('\\n', '\n').encode('utf-8')
    private_key = load_pem_private_key(data=private_key_pem, password=None)

    timestamp = int(time.time() * 1000)
    params["timestamp"] = timestamp

    # 파라미터들을 정렬 후 서명 <-> HTTP와 다름
    payload_for_sign = "&".join([f"{param}={value}" for param, value in sorted(params.items())])

    signature = base64.b64encode(private_key.sign(payload_for_sign.encode("ASCII")))
    params["signature"] = signature.decode("ASCII")

    payload = {
        "id": str(uuid.uuid4()),
        "method":method,
        "params": params
    }

    return payload

# https://developers.binance.com/docs/binance-spot-api-docs/rest-api/request-security
def get_signed_payload_post(user_id, params):
    private_key_str = get_key(user_id)["Private"]

    private_key_pem = private_key_str.replace('\\n', '\n').encode('utf-8')
    private_key = load_pem_private_key(data=private_key_pem, password=None)

    params["recvWindow"] = "5000"

    timestamp = str(int(time.time() * 1000))
    params["timestamp"] = timestamp

    # 파라미터들을 정렬하지 않고 서명 <-> WS와 다름
    payload_for_sign = "&".join([f"{param}={value}" for param, value in params.items()])

    signature = base64.b64encode(private_key.sign(payload_for_sign.encode("ASCII")))
    params["signature"] = signature.decode("ASCII")

    return params