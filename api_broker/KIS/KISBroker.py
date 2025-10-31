from ..BrokerCommon.BrokerInterface import BrokerInterface
from .constants import WS_URL, COLUMN_TO_KOR_DICT
from .ws_token_manager import get_ws_token
from typing import List, Dict, Any, Callable, Awaitable
import websockets
import json
import traceback
import asyncio

# 같은 app key로 2개 이상의 소켓을 동시에 사용할 수 없음
# -> 하나의 소켓에서 호가와 체결가를 동시에 가져올수는 있음(최대 41건, 2025-11-01 기준)
# {"header":{"tr_id":"(null)","tr_key":"","encrypt":"N"},"body":{"rt_cd":"9","msg_cd":"OPSP8996","msg1":"ALREADY IN USE appkey"}}
class KISBroker(BrokerInterface):
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.ws = None
        self.ws_thread = None
        self.orderbook_callback = None

        self.ws_orderbook = None

    def get_account_assets(self) -> List[Dict[str, Any]]:
        return [
            {
                'symbol': 'BTC',
                'balance': 0.5,
                'available': 0.5,
                'locked': 0.0,
                'avg_buy_price': 50000.0,
                'type': 'crypto'
            }
        ]
    
    def get_realtime_orderbook_price(self, symbol: str) -> Dict[str, Any]:
        return {
            'symbol': symbol,
            'price': 50000.0,
            'timestamp': '2025-01-01T00:00:00Z'
        }
    
    def place_order(self, symbol: str, side: str, quantity: float, price: float = None) -> Dict[str, Any]:
        return {
            'order_id': '12345',
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'status': 'pending'
        }
    
    async def subscribe_orderbook_async(self, ticker_symbol: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        try:
            url = WS_URL + "/ws/tryitout/HDFSASP0"
            async with websockets.connect(url, ping_interval=30) as ws:
                payload = {
                    "header": {
                        "approval_key": get_ws_token(),
                        "custtype": "P",
                        "tr_type": "1",
                        "content-type": "utf-8",
                    },
                    "body": {
                        "input": {
                            "tr_id": "HDFSASP0",
                            "tr_key": "DNASNVDA",
                        }
                    }
                }
                await ws.send(json.dumps(payload))

                payload = {
                    "header": {
                        "approval_key": get_ws_token(),
                        "custtype": "P",
                        "tr_type": "1",
                        "content-type": "utf-8",
                    },
                    "body": {
                        "input": {
                            "tr_id": "HDFSCNT0",
                            "tr_key": "DNASNVDA",
                        }
                    }
                }
                await ws.send(json.dumps(payload))

                print(f"✅ Subscribed to Binance {ticker_symbol} orderbook")

                while True:
                    try:
                        resp = await ws.recv()

                        # 데이터는 0으로 시작
                        if resp[0] == "0" or resp[0] == "1":
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

                            meta_data = resp.split("|")
                            tr_id = meta_data[1]
                            
                            real_data = resp.split("|")[-1].split("^")

                            resp_dict = {}
                            for col, value in zip(columns, real_data):
                                resp_dict[COLUMN_TO_KOR_DICT[col]] = value

                            normalized_data = {
                                "symbol": ticker_symbol,
                                "bids": [
                                    {"price": float(resp_dict["매수호가1"]), "quantity": float(resp_dict["매수잔량1"])}
                                ],
                                "asks": [
                                    {"price": float(resp_dict["매도호가1"]), "quantity": float(resp_dict["매도잔량1"])}
                                ],
                            }
                            
                            # 콜백 호출 - 예외 발생 시 루프 종료
                            await callback(normalized_data)
                        # 나머지는 그냥 json
                        else:
                            json_data = json.loads(resp)
                            if(json_data["header"]["tr_id"] == "PINGPONG"):
                                await ws.pong(resp)
                                print("Pong!")
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                    except asyncio.CancelledError:
                        # 취소 신호 - 즉시 종료
                        raise
                    except Exception as e:
                        # 콜백 오류 (연결 끊김 등) - 조용히 종료
                        print(f"Exception: {e}")
                        print(traceback.format_exc())
                        raise asyncio.CancelledError("Callback error")
        
        except asyncio.CancelledError:
            # 정상적인 취소 - 로그 없음
            pass
        except websockets.exceptions.ConnectionClosed:
            # Binance 연결 종료 - 로그 없음
            pass
        except Exception as e:
            print(f"❌ Binance WebSocket error: {e}")
            import traceback
            traceback.print_exc()
            print(traceback.format_exc())

    async def subscribe_trade_price_async(self, ticker_symbol: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        try:
            url = WS_URL + "/ws/tryitout/HDFSCNT0"
            async with websockets.connect(url, ping_interval=30) as ws:
                payload = {
                    "header": {
                        "approval_key": get_ws_token(),
                        "custtype": "P",
                        "tr_type": "1",
                        "content-type": "utf-8",
                    },
                    "body": {
                        "input": {
                            "tr_id": "HDFSCNT0",
                            "tr_key": "DNASNVDA",
                        }
                    }
                }
                await ws.send(json.dumps(payload))

                while True:
                    try:
                        resp = await ws.recv()
                        print(resp)

                        # 데이터는 0으로 시작
                        if resp[0] == "0":
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

                            meta_data = resp.split('|')[0]
                            real_data = resp.split('|')[-1].split("^")

                            resp_dict = {}
                            for col, value in zip(columns, real_data):
                                resp_dict[COLUMN_TO_KOR_DICT[col]] = value
                            
                            normalized_data = {
                                "symbol": resp_dict["종목코드"],
                                "price": resp_dict["매수호가"],
                                "quantity": resp_dict["체결량"],
                                "time": resp_dict["한국시간"],
                                "isBuyerMaker": True,
                                "timestamp": 1,
                            }
                            
                            # 콜백 호출 - 예외 발생 시 루프 종료
                            await callback(normalized_data)
                        # 나머지는 그냥 json
                        else:
                            json_data = json.loads(resp)
                            if(json_data["header"]["tr_id"] == "PINGPONG"):
                                await ws.pong(resp)
                                #print("Pong!")
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                    except asyncio.CancelledError:
                        # 취소 신호 - 즉시 종료
                        raise
                    except Exception as e:
                        # 콜백 오류 (연결 끊김 등) - 조용히 종료
                        print(f"Exception: {e}")
                        print(traceback.format_exc())
                        raise asyncio.CancelledError("Callback error")
        
        except asyncio.CancelledError:
            # 정상적인 취소 - 로그 없음
            pass
        except websockets.exceptions.ConnectionClosed:
            # Binance 연결 종료 - 로그 없음
            pass
        except Exception as e:
            print(f"❌ Binance WebSocket error: {e}")
            import traceback
            traceback.print_exc()
            print(traceback.format_exc())