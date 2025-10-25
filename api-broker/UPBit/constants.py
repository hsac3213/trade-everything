import os

API_URL = "https://api.upbit.com"

WS_PRICE_URL = "wss://api.upbit.com/websocket/v1"
WS_ASSET_URL = "wss://api.upbit.com/websocket/v1/private"

APP_KEY = os.environ.get("UPBIT_APP")
SEC_KEY = os.environ.get("UPBIT_SEC")