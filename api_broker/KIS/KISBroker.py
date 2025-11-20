from ..BrokerCommon.BrokerInterface import BrokerInterface
from .constants import API_URL, WS_URL, COLUMN_TO_KOR_DICT
from .ws_token_manager import get_ws_token
from .token_manager import get_access_token, get_key
from ..Common.Debug import *
from .order import place_order, cancel_order
from typing import List, Dict, Any, Callable, Awaitable
from typing import TypedDict, Literal
import websockets
import json
import asyncio
import requests
import pandas as pd
import traceback
from pprint import pprint
from datetime import datetime

# [ 종목 코드 파일 ]
# 아래 파일은 업데이트될 가능성이 있음에 유의
KIS_TICKERS_PATH = "./KIS/NASMST.COD"

# 같은 app key로 2개 이상의 소켓을 동시에 사용할 수 없음
# -> 하나의 소켓에서 호가와 체결가를 동시에 가져올수는 있음(최대 41건, 2025-11-01 기준)
# -> 오류 응답은 다음과 같음
# {"header":{"tr_id":"(null)","tr_key":"","encrypt":"N"},"body":{"rt_cd":"9","msg_cd":"OPSP8996","msg1":"ALREADY IN USE appkey"}}

# 2025-11-19(수) 기준 최대 41개 구독 가능
# -> 한 웹소켓에서 구독해야 함에 유의!
class KISWebSocket():
    def __init__(self):
        # 공유 웹소켓 task
        self.ws_task: Any = None
        # 공유 웹소켓
        self.ws: Any = None
        # 심볼(티커) 리스트
        self.symbols = []
        # 콜백 등록/삭제를 위한 lock
        self.callbacks_lock = asyncio.Lock()
        # 콜백 리스트
        # -> 콜백 리스트가 비어있으면 웹소켓 close 해야 함!
        self.orderbook_callbacks = []
        self.trade_callbacks = []

class KISBroker(BrokerInterface):
    # 클래스 레벨 공유 WebSocket 관리 (모든 인스턴스가 공유)

    # 각 사용자(user_id)에게 할당된 웹소켓 관리
    _user_lock: Dict[str, asyncio.Lock] = {}
    _user_ws: Dict[str, KISWebSocket] = {}
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id

        #print("[ KISBroker ]")
        #print(f"user_id : {user_id}")

    def place_order(self, order) -> List[Dict[str, Any]]:
        """
        KIS 주문 전송
        """
        pass
        #return place_order(self.user_id, order)
    
    def cancel_order(self, order) -> List[Dict[str, Any]]:
        """
        KIS 주문 취소
        """
        return cancel_order(self.user_id, order)

    def get_orders(self):
        """
        KIS 미체결 주문 목록
        """
        try:
            params = {
                "CANO": get_key(self.user_id)["account_number_0"],
                "ACNT_PRDT_CD": get_key(self.user_id)["account_number_1"],
                "OVRS_EXCG_CD": "NASD",
                "SORT_SQN": "DS",
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK200": "",
            }

            headers = {
                "content-type": "application/json; charset=utf-8",
                "authorization": "Bearer " + get_access_token(self.user_id),
                "appkey": get_key(self.user_id)["app_key"],
                "appsecret": get_key(self.user_id)["sec_key"],
                "tr_id": "TTTS3018R",
                "custtype": "P",
            }

            url = API_URL + f"/uapi/overseas-stock/v1/trading/inquire-nccs"
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp_json = resp.json()

            orders = []
            for order in resp_json["output"]:
                orders.append({
                    "order_id": order["odno"],
                    "symbol": order["pdno"],
                    # BUY(02) or SELL(01)
                    "side": "buy" if str(order["sll_buy_dvsn_cd"]) == "02" else "sell",
                    "price": order["ft_ord_unpr3"],
                    "amount": order["nccs_qty"],
                })

            return orders
        except requests.exceptions.RequestException as e:
            Error("KIS requests.exceptions.RequestException")
            print(e)
            return []
        except Exception as e:
            Error("KIS Exception")
            print(e)
            traceback.print_exc()
            return []

    def get_candle(self, symbol: str, interval: str, end_time: str = None):
        try:
            symbol = symbol.upper()
            interval = interval.lower()

            # 일봉 조회
            if interval == "1d":
                # KST datetime 문자열 형식 변환(YYYYMMDD)
                end_time_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                end_time_str = end_time_dt.strftime("%Y%m%d")

                url = API_URL + "/uapi/overseas-price/v1/quotations/dailyprice"
                params = {
                    "AUTH": "",
                    "EXCD": "NAS",
                    "SYMB": symbol.upper(),
                    "GUBN": "0",
                    "BYMD": end_time_str,
                    "MODP": "1",
                }

                headers = {
                    "content-type": "application/json; charset=utf-8",
                    "authorization": "Bearer " + get_access_token(self.user_id),
                    "appkey": get_key(self.user_id)["app_key"],
                    "appsecret": get_key(self.user_id)["sec_key"],
                    "tr_id": "HHDFS76240000",
                    "custtype": "P",
                }

                resp = requests.get(url, params=params, headers=headers,  timeout=10)
                resp.raise_for_status()     
                resp_json = resp.json()

                #resp_json["output2"].reverse()
                candles = []
                for row in resp_json["output2"]:
                    open_time_date = datetime.strptime(row["xymd"], "%Y%m%d")
                    open_time_timestamp = open_time_date.timestamp()

                    candles.append({
                        # lightweight-charts는 초 단위 timestamp 필요
                        "time": int(open_time_timestamp),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["clos"]),
                        # 거래금액 (Quote Asset Volume)
                        "volume": float(row["tvol"]),
                    })

                return candles
            # 시봉 조회
            elif interval == "1h":
                # KST datetime 문자열 형식 변환(YYYYMMDD)
                end_time_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                end_time_str = end_time_dt.strftime("%Y%m%d")

                url = API_URL + "/uapi/overseas-price/v1/quotations/inquire-time-itemchartprice"
                params = {
                    "AUTH": "",
                    "EXCD": "NAS",
                    "SYMB": symbol.upper(),
                    # 60분봉
                    "NMIN": "60",
                    # 전일 포함 여부(1)
                    "PINC": "1",
                    # 처음 조회 여부
                    "NEXT": "",
                    # 요청 개수(최대 120개)
                    "NREC": "120",
                    "FILL": "",
                    "KEYB": "",
                }

                headers = {
                    "content-type": "application/json; charset=utf-8",
                    "authorization": "Bearer " + get_access_token(self.user_id),
                    "appkey": get_key(self.user_id)["app_key"],
                    "appsecret": get_key(self.user_id)["sec_key"],
                    "tr_id": "HHDFS76950200",
                    "custtype": "P",
                }

                resp = requests.get(url, params=params, headers=headers,  timeout=10)
                resp.raise_for_status()     
                resp_json = resp.json()

                #resp_json["output2"].reverse()
                candles = []
                for row in resp_json["output2"]:
                    open_time_date = datetime.strptime(row["kymd"] + " " + row["khms"], "%Y%m%d %H%M%S")
                    open_time_timestamp = open_time_date.timestamp()

                    candles.append({
                        # lightweight-charts는 초 단위 timestamp 필요
                        "time": int(open_time_timestamp),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["last"]),
                        # 체결량
                        "volume": float(row["evol"]),
                    })

                return candles
            
        except requests.exceptions.RequestException as e:
            Error("[ KIS ]")
            Error("requests.exceptions.RequestException")
            return []
        except Exception as e:
            Error("[ KIS ]")    
            traceback.print_exc()
            return []

    @staticmethod
    async def _ws_connect(user_id: str):
        """웹소켓 연결(Backend <-> KIS)"""
        if user_id == None:
            Error("KIS invalid user_id.")
            return

        # Lock이 없는 경우 생성
        if user_id not in KISBroker._user_lock:
            KISBroker._user_lock[user_id] = asyncio.Lock()

        async with KISBroker._user_lock[user_id]:
            # 웹소켓 공유 정보 데이터가 없는 경우 생성
            if user_id not in KISBroker._user_ws:
                KISBroker._user_ws[user_id] = KISWebSocket()
            # 웹소켓 연결이 없는 경우 생성
            if KISBroker._user_ws[user_id].ws_task == None:
                # ping_interval은 사용하지 않을 것을 권장하고 있음
                # https://apiportal.koreainvestment.com/community/10000000-0000-0011-0000-000000000002/post/07f312e5-0bf3-4bbe-8179-1ffd7246b392
                KISBroker._user_ws[user_id].ws = await websockets.connect(WS_URL, ping_interval=None)
                KISBroker._user_ws[user_id].ws_task = asyncio.create_task(KISBroker._ws_loop(user_id))
            else:
                Info("Use existed ws.")
    
    @staticmethod
    async def _ws_loop(user_id):
        """웹소켓 루프(Backend <-> KIS)"""
        try:
            ws = KISBroker._user_ws[user_id].ws
            while True:
                try:
                    resp = await ws.recv()
                    await KISBroker._handle_ws_message(user_id, resp)
                    
                except asyncio.CancelledError:
                    Error("KIS LOOP asyncio.CancelledError")
                    print(KISBroker._user_ws[user_id].orderbook_callbacks)
                    # raise 하면 웹소켓 연결이 끊어짐 
                    #raise
                except websockets.exceptions.ConnectionClosedError:
                    Error("KIS LOOP websockets.exceptions.ConnectionClosedError")
                    #break
                except Exception as e:
                    Info("KIS LOOP Exception")
                    traceback.print_exc()
                        
        except asyncio.CancelledError:
            Error("KIS asyncio.CancelledError")
        except websockets.exceptions.ConnectionClosed:
            Error("KIS websockets.exceptions.ConnectionClosed")
        except websockets.exceptions.ConnectionClosedError:
            Error("KIS websockets.exceptions.ConnectionClosedError")
        except Exception as e:
            Error("KIS Exception")
            traceback.print_exc()
        finally:
            Error("KIS disconnected.")
    
    @staticmethod
    async def _handle_ws_message(user_id: str, resp: str):
        """웹소켓 메시지 핸들러(Backend <-> KIS)"""
        # 핑 메시지 처리
        if resp[0] not in ["0", "1"]:
            try:
                json_data = json.loads(resp)
                if json_data.get("header", {}).get("tr_id") == "PINGPONG":
                    await KISBroker._user_ws[user_id].ws.pong(resp)
                    #Info("KIS Ping processed.")
                else:
                    pass
                    #Info("KIS WS Message")
                    #pprint(json_data)
            except json.JSONDecodeError:
                Error("KIS json.JSONDecodeError")
                pass
            return

        # 데이터 메시지 - tr_id로 구분
        meta_data = resp.split("|")
        if len(meta_data) < 2:
            return
        
        tr_id = meta_data[1]
        
        # 호가 데이터 처리(HDFSASP0)
        if tr_id == "HDFSASP0":
            await KISBroker._handle_orderbook(user_id, resp)
        
        # 체결가 데이터 처리(HDFSCNT0)
        elif tr_id == "HDFSCNT0":
            await KISBroker._handle_trade(user_id, resp)
    
    @staticmethod
    async def _handle_orderbook(user_id: str, resp: str):
        """호가 데이터 처리"""
        try:
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
            
            real_data = resp.split("|")[-1].split("^")
            
            if len(real_data) < len(columns):
                return
            
            resp_dict = {COLUMN_TO_KOR_DICT[col]: value for col, value in zip(columns, real_data)}
            
            normalized_data = {
                "symbol": resp_dict["종목코드"].replace("DNAS", ""),
                "bids": [
                    {"price": float(resp_dict["매수호가1"]), "quantity": float(resp_dict["매수잔량1"])}
                ],
                "asks": [
                    {"price": float(resp_dict["매도호가1"]), "quantity": float(resp_dict["매도잔량1"])}
                ],
            }
            #print(normalized_data["asks"])
            
            # 콜백 리스트 호출
            async with KISBroker._user_ws[user_id].callbacks_lock:
                # 안전한 원소 제거를 위하여 리스트 복사
                callbacks_copy = KISBroker._user_ws[user_id].orderbook_callbacks[:]
                for callback in callbacks_copy:
                    try:
                        await callback(normalized_data)
                    except asyncio.CancelledError:
                        # 연결 해제된 callback 제거
                        try:
                            if callback in KISBroker._user_ws[user_id].orderbook_callbacks:
                                KISBroker._user_ws[user_id].orderbook_callbacks.remove(callback)
                                break
                        except:
                            Error("Failed to remove callback.")
                    except Exception as e:
                        Error("KIS Exception")
                        print(f"e : {e}")
            
        except Exception as e:
            print(f"❌ Error parsing orderbook: {e}")
    
    @staticmethod
    async def _handle_trade(user_id: str, resp: str):
        """체결가 데이터 처리"""
        try:
            columns = [
                "RSYM",
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
            
            real_data = resp.split('|')[-1].split("^")
            
            if len(real_data) < len(columns):
                return
            
            resp_dict = {COLUMN_TO_KOR_DICT[col]: value for col, value in zip(columns, real_data)}

            normalized_data = {
                "symbol": resp_dict["종목코드"].replace("DNAS", ""),
                "price": float(resp_dict["현재가"]) if resp_dict["현재가"] else 0.0,
                "quantity": float(resp_dict["체결량"]) if resp_dict["체결량"] else 0.0,
                "time": resp_dict["한국시간"],
                "isBuyerMaker": True,
                "timestamp": int(asyncio.get_event_loop().time() * 1000),
            }
            
            # 콜백 리스트 호출
            async with KISBroker._user_ws[user_id].callbacks_lock:
                # 안전한 원소 제거를 위하여 리스트 복사
                callbacks_copy = KISBroker._user_ws[user_id].trade_callbacks[:]
                for callback in callbacks_copy:
                    try:
                        await callback(normalized_data)
                    except asyncio.CancelledError:
                        # 연결 해제된 callback 제거
                        try:
                            if callback in KISBroker._user_ws[user_id].trade_callbacks:
                                KISBroker._user_ws[user_id].trade_callbacks.remove(callback)
                                continue
                        except:
                            Error("Failed to remove callback.")
                    except Exception as e:
                        Error("KIS Exception")
                        print(f"e : {e}")
            
        except Exception as e:
            print(f"❌ Error parsing trade: {e}")
    
    async def subscribe_orderbook_async(self, user_id: str, ticker_symbol: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        """실시간 호가 구독(Frontend <-> Backend)"""
        try:
            ticker_symbol = "DNAS" + ticker_symbol.upper()
            print(ticker_symbol)
            # 웹소켓 연결
            await KISBroker._ws_connect(user_id)

            # 호가 구독
            payload = {
                "header": {
                    "approval_key": get_ws_token(user_id),
                    "custtype": "P",
                    "tr_type": "1",
                    "content-type": "utf-8",
                },
                "body": {
                    "input": {
                        "tr_id": "HDFSASP0",
                        "tr_key": ticker_symbol,
                    }
                }
            }
            await KISBroker._user_ws[user_id].ws.send(json.dumps(payload))

            # 호가 콜백 등록
            async with KISBroker._user_ws[user_id].callbacks_lock:
                KISBroker._user_ws[user_id].orderbook_callbacks.append(callback)

            while True:
                await asyncio.sleep(1.0)
                
        except asyncio.CancelledError:
            Error("KIS asyncio.CancelledError")
            raise
        except Exception as e:
            Info("KIS Exception")
            print(f"e : {e}")
            traceback.print_exc()
        finally:
            # 호가 콜백 제거
            Info("Finally")
            try:
                async with KISBroker._user_ws[user_id].callbacks_lock:
                    if callback in KISBroker._user_ws[user_id].orderbook_callbacks:
                        KISBroker._user_ws[user_id].orderbook_callbacks.remove(callback)
            except:
                Error("Failed to remove callback.")

    async def subscribe_trade_price_async(self, user_id: str, ticker_symbol: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        """실시간 체결가 구독(Frontend <-> Backend)"""
        ticker_symbol = "DNAS" + ticker_symbol.upper()
        try:
            # 웹소켓 연결
            await KISBroker._ws_connect(user_id)

            # 체결가 구독
            async with KISBroker._user_lock[user_id]:
                payload = {
                    "header": {
                        "approval_key": get_ws_token(user_id),
                        "custtype": "P",
                        "tr_type": "1",
                        "content-type": "utf-8",
                    },
                    "body": {
                        "input": {
                            "tr_id": "HDFSCNT0",
                            "tr_key": ticker_symbol,
                        }
                    }
                }
                await KISBroker._user_ws[user_id].ws.send(json.dumps(payload))

            # 체결가 콜백 등록
            async with KISBroker._user_ws[user_id].callbacks_lock:
                KISBroker._user_ws[user_id].trade_callbacks.append(callback)

            while True:
                await asyncio.sleep(1.0)
                
        except asyncio.CancelledError:
            Error("KIS asyncio.CancelledError")
            raise
        except Exception as e:
            Info("KIS Exception")
            print(f"e : {e}")
            traceback.print_exc()
        finally:
            # 체결가 콜백 제거
            Info("Finally")
            try:
                async with KISBroker._user_ws[user_id].callbacks_lock:
                    if callback in KISBroker._user_ws[user_id].trade_callbacks:
                        KISBroker._user_ws[user_id].trade_callbacks.remove(callback)
            except:
                Error("Failed to remove callback.")

    def get_symbols(self) -> List[Dict[str, Any]]:
        try:
            df = pd.read_table(KIS_TICKERS_PATH, sep="\t",encoding="cp949", header=None)
            
            symbols = []
            for row in df.itertuples():
                if pd.notna(row[5]) and pd.notna(row[8]):
                    symbols.append({
                        "symbol": row[5],
                        "display_name": row[8]
                    })
                else:
                    print(row)
            
            return symbols
        except requests.exceptions.RequestException as e:
            print(f"Error fetching symbols from Binance: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error in get_symbols: {e}")
            import traceback
            traceback.print_exc()
            return []

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