import os

API_URL = "https://api.binance.com"
WSS_URL = "wss://stream.binance.com:9443"
WS_URL = "wss://ws-api.binance.com:443/ws-api/v3"

API_KEY = os.environ.get("BINANCE_API")
SEC_KEY = os.environ.get("BINANCE_SEC")

BINANCE_ED25519_API_KEY = os.environ.get("BINANCE_ED25519_API_KEY")

BINANCE_PRIVATE_KEY_PATH = os.environ.get("BINANCE_PRIVATE_KEY_PATH")

# 암호화폐 거래 쌍 화이트 리스트
# -> 화이트 리스트 이외의 거래 쌍에 대해서는 모든 요청 거부
CRYPTO_PAIR_WHITELIST = [
    "btcusdt"
]