from constants import WS_URL, COLUMN_TO_KOR_DICT
from ws_token_manager import get_ws_token
import websockets
import asyncio
import json

async def get_realtime_orderbook_price(stock_code):
    async with websockets.connect(WS_URL + "/tryitout/HDFSASP0", ping_interval=30) as ws:
        send_data = json.dumps({
            "header": {
                "approval_key": get_ws_token(),
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8",
            },
            "body": {
                "input": {
                    "tr_id": "HDFSASP0",
                    "tr_key": stock_code,
                }
            }
        })
        await ws.send(send_data)

        while True:
            data = await ws.recv()
            # 데이터는 0으로 시작
            if data[0] == "0":
                columns = [
                    "rsym",
                    "symb",
                    "zdiv",
                    "xymd",
                    "xhms",
                    "kymd",
                    "khms",
                    "bvol",
                    "avol",
                    "bdvl",
                    "advl",
                    "pbid1",
                    "pask1",
                    "vbid1",
                    "vask1",
                    "dbid1",
                    "dask1"
                ]

                meta_data = data.split('|')[0]
                real_data = data.split('|')[-1].split("^")

                for col, value in zip(columns, real_data):
                    print(f"{COLUMN_TO_KOR_DICT[col]} : {value}")
                print("")
            # 나머지는 그냥 json
            else:
                json_data = json.loads(data)
                if(json_data["header"]["tr_id"] == "PINGPONG"):
                    await ws.pong(data)
                    print("Pong!")

async def get_realtime_transaction_price(stock_code):
    async with websockets.connect(WS_URL + "/tryitout/HDFSCNT0", ping_interval=30) as ws:
        send_data = json.dumps({
            "header": {
                "approval_key": get_ws_token(),
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8",
            },
            "body": {
                "input": {
                    "tr_id": "HDFSCNT0",
                    "tr_key": stock_code,
                }
            }
        })
        await ws.send(send_data)

        while True:
            data = await ws.recv()
            print(data)
            # 데이터는 0으로 시작
            if data[0] == "0":
                columns = [
                    "SYMB",
                    "ZDIV",
                    "TYMD",
                    "XYMD",
                    "XHMS",
                    "KYMD",
                    "KHMS",
                    "OPEN",
                    "HIGH",
                    "LOW",
                    "LAST",
                    "SIGN",
                    "DIFF",
                    "RATE",
                    "PBID",
                    "PASK",
                    "VBID",
                    "VASK",
                    "EVOL",
                    "TVOL",
                    "TAMT",
                    "BIVL",
                    "ASVL",
                    "STRN",
                    "MTYP"
                ]

                meta_data = data.split('|')[0]
                real_data = data.split('|')[-1].split("^")

                for col, value in zip(columns, real_data):
                    print(f"{COLUMN_TO_KOR_DICT[col]} : {value}")
                print("")
            # 나머지는 그냥 json
            else:
                json_data = json.loads(data)
                if(json_data["header"]["tr_id"] == "PINGPONG"):
                    await ws.pong(data)
                    print("Pong!")

#asyncio.run(get_realtime_orderbook("DNASAAPL"))
#asyncio.run(get_realtime_transaction_price("DNASAAPL"))