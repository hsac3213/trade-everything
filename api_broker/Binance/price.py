from .common import WSS_URL, CRYPTO_PAIR_WHITELIST
import websockets
import asyncio
import json

async def get_realtime_orderbook_price(crypto_pair):
    if crypto_pair not in CRYPTO_PAIR_WHITELIST:
        return
    async with websockets.connect(WSS_URL + "/ws", ping_interval=30) as ws:
        send_data = json.dumps({
            "method": "SUBSCRIBE",
            "params": [
                f"{crypto_pair}@depth20@100ms"
            ],
            "id": "1"
        })
        await ws.send(send_data)

        while True:
            data = await ws.recv()
            print(data)

async def get_realtime_trade_price(crypto_pair):
    if crypto_pair not in CRYPTO_PAIR_WHITELIST:
        return
    async with websockets.connect(WSS_URL + "/ws", ping_interval=30) as ws:
        send_data = json.dumps({
            "method": "SUBSCRIBE",
            "params": [
                f"{crypto_pair}@aggTrade"
            ],
            "id": "1"
        })
        await ws.send(send_data)

        while True:
            data = await ws.recv()
            print(data)

#asyncio.run(get_realtime_orderbook_price("btcusdt"))
#asyncio.run(get_realtime_trade_price("btcusdt"))