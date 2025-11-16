import os
import time
import hmac, hashlib, base64, uuid
from cryptography.hazmat.primitives.serialization import load_pem_private_key

API_URL = "https://api.binance.com"
WSS_URL = "wss://stream.binance.com:9443"
WS_URL = "wss://ws-api.binance.com:443/ws-api/v3"

BINANCE_ED25519_API_KEY = os.environ.get("BINANCE_ED25519_API_KEY")

BINANCE_PRIVATE_KEY_PATH = os.environ.get("BINANCE_PRIVATE_KEY_PATH")

# 암호화폐 거래 쌍 화이트 리스트
# -> 화이트 리스트 이외의 거래 쌍에 대해서는 모든 요청 거부
CRYPTO_PAIR_WHITELIST = [
    "btcusdt"
]

# https://github.com/binance/binance-signature-examples/tree/master/python
def signing(input):
    signature = hmac.new(SEC_KEY.encode("utf-8"), input.encode("utf-8"), hashlib.sha256)
    signature = signature.hexdigest()
    return signature

# https://developers.binance.com/docs/binance-spot-api-docs/websocket-api/request-security
def get_signed_payload_ws(method, params):
    private_key = ""
    with open(BINANCE_PRIVATE_KEY_PATH, "rb") as f:
        private_key = load_pem_private_key(data=f.read(), password=None)

    timestamp = int(time.time() * 1000)
    params["timestamp"] = timestamp

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
def get_signed_payload_post(params):
    private_key = ""
    with open(BINANCE_PRIVATE_KEY_PATH, "rb") as f:
        private_key = load_pem_private_key(data=f.read(), password=None)

    params["recvWindow"] = "5000"

    timestamp = str(int(time.time() * 1000))
    params["timestamp"] = timestamp

    payload_for_sign = "&".join([f"{param}={value}" for param, value in params.items()])

    signature = base64.b64encode(private_key.sign(payload_for_sign.encode("ASCII")))
    params["signature"] = signature.decode("ASCII")

    return params