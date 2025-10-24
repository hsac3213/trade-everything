from constants import WS_URL
from ws_token_manager import get_ws_token
import websockets
import asyncio

async def get_realtime_stock_price(stock_name):
    # 해외주식(미국) 호가, 체결가, 체결통보
    code_list = [['1','HDFFF010','DNASAAPL']]

    senddata_list=[]
    for i, j, k in code_list:
        temp = '{"header":{"approval_key": "%s","custtype":"P","tr_type":"%s","content-type":"utf-8"},"body":{"input":{"tr_id":"%s","tr_key":"%s"}}}'%(get_ws_token(), i, j, k)
        senddata_list.append(temp)

    async with websockets.connect(WS_URL + "/tryitout/HDFFF010", ping_interval=None) as ws:
        for senddata in senddata_list:
            await ws.send(senddata)
            print(f"Input Command is :{senddata}")

        while True:
            data = await ws.recv()
            print(data)
            if data[0] == '0':
                recvstr = data.split('|')
                trid0 = recvstr[1]
                print(trid0)

asyncio.run(get_realtime_stock_price("AAPL"))