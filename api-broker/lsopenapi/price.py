from constants import WS_URL
from token_manager import get_access_token
import websockets
import asyncio
import json

async def get_realtime_orderbook_price(stock_code):
    async with websockets.connect(WS_URL + "/websocket", ping_interval=30) as ws:
        send_data = json.dumps({
            "header": {
                "token": get_access_token(),
                "tr_type": "3",
            },
            "body": {
                "tr_cd": "GSH",
                "tr_key": "81SOXL            "
            }
        })
        await ws.send(send_data)

        while True:
            data = await ws.recv()
            print(data)

asyncio.run(get_realtime_orderbook_price("DNASAAPL"))