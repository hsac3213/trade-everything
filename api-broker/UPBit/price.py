from constants import *
import jwt
import uuid
import json
import asyncio
import websockets
import time

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

        # 응답 속도 측정 변수
        message_count = 0
        start_time = time.time()
        last_print_time = start_time

        while True:
            data = await ws.recv()
            message_count += 1
            
            current_time = time.time()
            elapsed = current_time - last_print_time
            rate = message_count / elapsed
            print(f"WebSocket 응답 속도: {rate:.2f} 회/초 (총 {message_count}개 메시지)")
            
            #print(data)

#asyncio.run(test())