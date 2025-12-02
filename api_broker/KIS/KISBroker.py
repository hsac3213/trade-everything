from ..BrokerCommon.BrokerInterface import BrokerInterface
from ..BrokerCommon.BrokerData import *
from .constants import API_URL, WS_URL, COLUMN_TO_KOR_DICT, DAY_MARKET_TIME
from .constants import check_market_time
from .common import aes_decrypt
from .ws_token_manager import get_ws_token
from .token_manager import get_access_token, get_key
from ..Common.Debug import *
from .order import place_order, cancel_order
from .account import get_assets
from typing import List, Dict, Any, Callable, Awaitable
from typing import TypedDict, Literal
import websockets
import json
import asyncio
import requests
import pandas as pd
import traceback
from pprint import pprint
from datetime import datetime, timedelta, time, date

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

        self.order_update_callback = None
        self.aes_decrypt_key = None
        self.aes_decrypt_iv = None

class KISBroker(BrokerInterface):
    # 클래스 레벨 공유 WebSocket 관리 (모든 인스턴스가 공유)

    # 각 사용자(user_id)에게 할당된 웹소켓 관리
    _user_lock: Dict[str, asyncio.Lock] = {}
    _user_ws: Dict[str, KISWebSocket] = {}
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self.broker_name = "KIS"

        #print("[ KISBroker ]")
        #print(f"user_id : {user_id}")

    def get_assets(self) -> List[Dict[str, Any]]:
        """
        KIS 자산 조회
        """
        return get_assets(self.user_id)

    def get_candle(self, symbol: str, interval: str, end_time: str = None):
        """
        KIS 캔들 조회
        """
        try:
            # 일봉 조회
            if interval == "1d":
                LIMIT = 100
                symbol = symbol.upper()

                end_time_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                # 현재 시각을 초과하는 요청 불가
                end_time_dt = min(end_time_dt, datetime.now())

                # 임의의 KST 시각을 KST 정각 시각으로 변환하고 Start Time 계산
                if interval == "1d":
                    end_time_dt = end_time_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    start_time_dt = end_time_dt + timedelta(days=-LIMIT)
                elif interval == "1h":
                    end_time_dt = end_time_dt.replace(minute=0, second=0, microsecond=0)
                    start_time_dt = end_time_dt + timedelta(hours=-LIMIT)
                else:
                    raise "Invalid interval."
                
                print("[ Param Start to End ]")
                print(f"str : {end_time}")
                print(f"{start_time_dt.strftime('%Y-%m-%d %H:%M:%S')} -> {end_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")

                # DB에서 캔들 데이터 가져오기(시간의 오름차순으로 정렬되어 있음)
                db_candles = get_candles_from_db(self.broker_name, symbol, interval, None, end_time)
                print(f"DB Candles Size : {len(db_candles)}")
                
                # DB에 요청된 범위의 캔들 데이터가 존재하는 경우
                if len(db_candles) > 0:
                    db_start_time_dt = db_candles[0]["open_time"]
                    db_end_time_dt = db_candles[-1]["open_time"]

                    # 현재 생성중인 캔들은 비교에서 제외
                    close_end_time_dt = end_time_dt
                    if interval == "1d":
                        close_end_time_dt = close_end_time_dt + timedelta(days=1)
                    elif interval == "1h":
                        close_end_time_dt = close_end_time_dt + timedelta(hours=1)

                    compare_end_time_dt = end_time_dt
                    if datetime.now() < compare_end_time_dt:
                        print(f"생성중인 캔들 무시")
                        if interval == "1d":
                            compare_end_time_dt = close_end_time_dt + timedelta(days=-2)
                        elif interval == "1h":
                            compare_end_time_dt = close_end_time_dt + timedelta(hours=-2)
                    print(f"compare_end_time_dt : {compare_end_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")

                    # 모든 데이터가 DB에 존재하는 경우
                    if db_start_time_dt <= start_time_dt and db_end_time_dt == compare_end_time_dt:
                        print("모든 데이터가 DB에 존재!")
                        final_candles = db_candles
                    # 일부 데이터만 DB에 존재하는 경우
                    else:
                        if db_start_time_dt <= start_time_dt:
                            # 마지막 캔들만 필요한 경우
                            if interval == "1d" and db_end_time_dt == (compare_end_time_dt + timedelta(days=-1)):
                                print(f"마지막 캔들만 가져오기({interval})")
                                api_candles = self.fetch_candles_from_api(symbol, interval, compare_end_time_dt)
                                final_candles = db_candles + api_candles
                            elif interval == "1h" and db_end_time_dt == (compare_end_time_dt + timedelta(hours=-1)):
                                print(f"마지막 캔들만 가져오기({interval})")
                                api_candles = self.fetch_candles_from_api(symbol, interval, compare_end_time_dt)
                                final_candles = db_candles + api_candles
                            # 다수의 캔들이 필요한 경우
                            else:
                                new_end_time_dt = end_time_dt
                                if interval == "1d":
                                    new_end_time_dt = new_end_time_dt + timedelta(days=1)
                                elif interval == "1h":
                                    new_end_time_dt = new_end_time_dt + timedelta(hours=1)
                                
                                print(f"[ 부족분 범위 ]")
                                print(f" -> {new_end_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                                
                                # 부족분 데이터 요청
                                api_candles = self.fetch_candles_from_api(symbol, interval, new_end_time_dt)
                                if len(api_candles) > 0:
                                    print("[ Fetched Start to End ]")
                                    print(f"{api_candles[0]["open_time"].strftime('%Y-%m-%d %H:%M:%S')} -> {api_candles[-1]["open_time"].strftime('%Y-%m-%d %H:%M:%S')}")
                                    
                                    # DB에 캔들 데이터 저장
                                    insert_candles_to_db(api_candles)
                                    # DB에 저장된 캔들 데이터에 API로 받은 캔들 데이터를 결합
                                    final_candles = db_candles + api_candles
                        # 전체 데이터 요청
                        else:
                            api_candles = self.fetch_candles_from_api(symbol, interval, end_time_dt)
                            if len(api_candles) > 0:
                                print("[ Fetched Start to End ]")
                                print(f"{api_candles[0]["open_time"].strftime('%Y-%m-%d %H:%M:%S')} -> {api_candles[-1]["open_time"].strftime('%Y-%m-%d %H:%M:%S')}")
                                
                                # DB에 캔들 데이터 저장
                                insert_candles_to_db(api_candles)
                                final_candles = api_candles
                            else:
                                print("[ 캔들 요청 실패! ]")
                                final_candles = []

                # DB에 요청된 범위의 캔들 데이터가 없는 경우
                else:
                    # 전체 데이터 요청
                    api_candles = self.fetch_candles_from_api(symbol, interval, end_time_dt)
                    if len(api_candles) > 0:
                        print("[ Fetched Start to End ]")
                        print(f"{api_candles[0]["open_time"].strftime('%Y-%m-%d %H:%M:%S')} -> {api_candles[-1]["open_time"].strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        # DB에 캔들 데이터 저장
                        insert_candles_to_db(api_candles)
                        final_candles = api_candles
                    else:
                        print("[ 캔들 요청 실패! ]")
                        final_candles = []

                # 중복 제거를 위한 딕셔너리 사용 (time을 키로 사용)
                unique_candles = {}
                for candle in final_candles:
                    candle_time = int(candle["open_time"].timestamp())
                    # 딕셔너리에 저장하여 중복된 시간의 캔들은 덮어씌움 (또는 건너뛰기 가능)
                    unique_candles[candle_time] = {
                        "time": candle_time,
                        "open": float(candle["open"]),
                        "high": float(candle["high"]),
                        "low": float(candle["low"]),
                        "close": float(candle["close"]),
                        "volume": float(candle["volume"]) if candle["volume"] != None else 0.0,
                    }

                normalized_candles = list(unique_candles.values())

                # open_time(time) 기준 오름차순 정렬
                normalized_candles.sort(key=lambda x: x["time"])

                print(f"Normalized Candles Size : {len(normalized_candles)}")
                return normalized_candles
            # 시간봉 조회
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
            else:
                return []
            
        except requests.exceptions.RequestException as e:
            Error("[ KIS ]")
            Error("requests.exceptions.RequestException")
            return []
        except Exception as e:
            Error("[ KIS ]")    
            traceback.print_exc()
            return []
        
    def fetch_candles_from_api(self, symbol: str, interval: str, end_time_dt: datetime = datetime.now()) -> List[Dict[str, Any]]:
        """
        KIS API에서 캔들 데이터 조회
        """
        try:
            Info("[ Requested Candles ]")
            print(f"interval : {interval}")
            print(f"end_time_dt : {end_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")

            # 임의의 KST 시각을 KST 정각 시각으로 변환
            api_end_time_dt = None
            if interval == "1d":
                api_end_time_dt = end_time_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            elif interval == "1h":
                api_end_time_dt = end_time_dt.replace(minute=0, second=0, microsecond=0)
            else:
                raise "Invalid interval."
            
            print(f"api_end_time_dt : {api_end_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 일봉 조회
            if interval == "1d":
                # KST datetime 형식 변환(YYYYMMDD)
                end_time_str = api_end_time_dt.strftime("%Y%m%d")

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
                    candles.append({
                        "broker_name": self.broker_name,
                        "symbol": symbol,
                        "interval": interval,
                        "open_time": datetime.strptime(row["xymd"], "%Y%m%d"),
                        "close_time": datetime.strptime(row["xymd"], "%Y%m%d") + timedelta(days=1) - timedelta(microseconds=1),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["clos"]),
                        "volume": float(row["tvol"]),
                        "quote_volume": float(row["tamt"]),
                        "trade_count": 0,
                        "taker_buy_base_asset_volume": float(0.0),
                        "taker_buy_quote_asset_volume": float(0.0),
                    })

                print(f"len(candles) : {len(candles)}")
                if len(candles) > 0:
                    print(f"First Candle : {candles[0]["open_time"].strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"Last Candle : {candles[-1]["open_time"].strftime('%Y-%m-%d %H:%M:%S')}")

                return candles
        except Exception as e:
            Error(f"Exception")
            traceback.print_exc()
            return []

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
            
            #Info("")
            #pprint(resp_json)

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
                Info("Use existing ws.")
    
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
                    #pprint(json_data)
                    # 실시간 체결통보 구독 성공
                    if "header" in json_data and "tr_id" in json_data["header"]:
                        if json_data["header"]["tr_id"] == "H0GSCNI0":
                            KISBroker._user_ws[user_id].aes_decrypt_key = json_data["body"]["output"]["key"]
                            KISBroker._user_ws[user_id].aes_decrypt_iv = json_data["body"]["output"]["iv"]
                            Info("실시간 체결통보 구독 성공")
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
        # 실시간체결통보 데이터 처리
        # [ 응답 형식 ]
        # 1|H0GSCNI0|001|(암호화 된 데이터)
        elif tr_id == "H0GSCNI0":
            Info(resp)
            # 암호화 된 데이터인지 확인
            if str(meta_data[0]) == "1":
                # 복호화 수행
                dec_resp = aes_decrypt(meta_data[3], KISBroker._user_ws[user_id].aes_decrypt_key, KISBroker._user_ws[user_id].aes_decrypt_iv)
                print(dec_resp)
        else:
            Info(resp)
        
    
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
        """KIS 실시간 호가 구독(Frontend <-> Backend)"""
        try:
            # 주간거래 시간 처리
            market_code = "DNAS"
            if check_market_time(DAY_MARKET_TIME):
                market_code = "RBAQ"

            ticker_symbol = market_code + ticker_symbol.upper()
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
        """KIS 실시간 체결가 구독(Frontend <-> Backend)"""
        try:
            # 주간거래 시간 처리
            market_code = "DNAS"
            if check_market_time(DAY_MARKET_TIME):
                market_code = "RBAQ"

            ticker_symbol = market_code + ticker_symbol.upper()

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

    async def subscribe_order_update_async(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        """
        KIS 실시간 주문 업데이트 구독
        -> 주문 접수/체결/취소 등
        """
        try:
            # 웹소켓 연결
            await KISBroker._ws_connect(self.user_id)

            # 실시간체결통보 구독
            async with KISBroker._user_lock[self.user_id]:
                payload = {
                    "header": {
                        "approval_key": get_ws_token(self.user_id),
                        "tr_type": "1",
                        "custtype": "P",
                        "content-type": "utf-8",
                    },
                    "body": {
                        "input": {
                            "tr_id": "H0GSCNI0",
                            "tr_key": get_key(self.user_id)["hts_id"],
                        }
                    }
                }
                resp = await KISBroker._user_ws[self.user_id].ws.send(json.dumps(payload))

            # 실시간체결통보 콜백 등록
            async with KISBroker._user_ws[self.user_id].callbacks_lock:
                self.order_update_callback = callback

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
            # 실시간체결통보 콜백 제거
            Info("Finally")
            try:
                async with KISBroker._user_ws[self.user_id].callbacks_lock:
                    self.order_update_callback = callback = None
                    KISBroker._user_ws[self.user_id].aes_decrypt_key = None
                    KISBroker._user_ws[self.user_id].aes_decrypt_iv = None
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