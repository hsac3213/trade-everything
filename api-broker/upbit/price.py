from constants import *
import jwt
import uuid
import json
import asyncio
import websockets

async def test():
    ticket = str(uuid.uuid4())
    payload = {
        'access_key': APP_KEY,
        'nonce': str(uuid.uuid4()),
    }

    jwt_token = jwt.encode(payload, SEC_KEY)
    authorization_token = f'Bearer {jwt_token}'
    headers = {"Authorization": authorization_token}

    async with websockets.connect(WS_PRICE_URL, additional_headers=headers, ping_interval=None) as ws:
        await ws.send(json.dumps([
            {
                "ticket": ticket,
            },
            {
                "type": "orderbook",
                "codes": ["KRW-BTC"],
                "level": 10000
            },
            {
                "format": "DEFAULT"
            }
        ]))
        print(f"Input Command is :{payload}")

        while True:
            data = await ws.recv()
            print(data)
            break

asyncio.run(test())