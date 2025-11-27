from ..BrokerCommon.BrokerInterface import BrokerInterface
from ..BrokerCommon.DataTypes import *
from ..BrokerCommon.BrokerData import *
from .common import API_URL, WSS_URL, WS_URL, get_key
from .common import get_signed_payload_ws, get_signed_payload_post
from .price import get_realtime_orderbook_price, get_realtime_trade_price
from .order import place_order, cancel_order, cancel_all_orders
from ..Common.Debug import *

from typing import List, Dict, Any, Callable, Awaitable
import websockets
import json
import asyncio
import requests
from datetime import datetime, timedelta, timezone
import time
from urllib.parse import urlencode
import uuid
import traceback

from pprint import pprint

# 웹소켓 하나를 계속 유지하고 구독과 해제를 한 소켓에서 수행하는 것도 고려해보기
# Binance는 IP 당 limit이 존재하므로 나중에는 클라이언트에서 웹소켓 스트림을 직접 구독하도록 수정하기
# 또는, 아래와 같은 이중 구조도 고려해볼 것
# -> 클라이언트의 웹소켓 : Display
# -> 서버의 웹소켓(24/7 연결 유지) : 서버 사이드 자동 거래 스크립트 등에 활용

# Endpoint 마다 rate limit 관리 코드 추가하기!!
# HTTP 429 return code is used when breaking a request rate limit.
# HTTP 418 return code is used when an IP has been auto-banned for continuing to send requests after receiving 429 codes.
# Ping 프레임 수신시 pong 프레임으로 응답 필요(Ping 프레임과 같은 내용으로)
# -> 라이브러리에서 자동으로 처리되는건가?

class BinanceBroker(BrokerInterface):
    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self.ws = None
        self.ws_thread = None
        self.orderbook_callback = None

        self.ws_orderbook = None

    def get_candle(self, symbol: str, interval: str, end_time: str = None):
        """
        Binance 캔들 조회
        """
        try:
            LIMIT = 1000
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
            #print(f"{start_time_dt.strftime('%Y-%m-%d %H:%M:%S')} -> {end_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")

            # DB에서 캔들 데이터 가져오기(시간의 오름차순으로 정렬되어 있음)
            db_candles = get_candles_from_db("Binance", symbol, interval, None, end_time)
            print("[ DB ]")
            print(f"DB Candles Size : {len(db_candles)}")
            if len(db_candles) > 0:
                print(f"DB Start Candle : {db_candles[0]["open_time"].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"DB End Candle : {db_candles[-1]["open_time"].strftime('%Y-%m-%d %H:%M:%S')}")
            
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
                            api_candles = self.fetch_candles_from_api(symbol, interval, None, end_time_dt, limit=1)
                            final_candles = db_candles + api_candles
                        elif interval == "1h" and db_end_time_dt == (compare_end_time_dt + timedelta(hours=-1)):
                            print(f"마지막 캔들만 가져오기({interval})")
                            api_candles = self.fetch_candles_from_api(symbol, interval, None, end_time_dt, limit=1)
                            final_candles = db_candles + api_candles
                        # DB에 캐싱된 캔들 데이터보다 미래 시점의 캔들이 필요한 경우
                        else:
                            new_start_time_dt = db_end_time_dt
                            if interval == "1d":
                                new_start_time_dt = new_start_time_dt + timedelta(days=1)
                            elif interval == "1h":
                                new_start_time_dt = new_start_time_dt + timedelta(hours=1)
                        
                            api_candles = self.fetch_candles_from_api(symbol, interval, new_start_time_dt, end_time_dt)
                            final_candles = db_candles + api_candles
                    # 다수의 캔들이 필요한 경우
                    else:
                        new_end_time_dt = db_start_time_dt
                        if interval == "1d":
                            new_end_time_dt = new_end_time_dt + timedelta(days=-1)
                        elif interval == "1h":
                            new_end_time_dt = new_end_time_dt + timedelta(hours=-1)
                        
                        print(f"[ 부족분 범위 ]")
                        print(f"? -> {new_end_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        # 부족분 데이터 요청
                        api_candles = self.fetch_candles_from_api(symbol, interval, None, new_end_time_dt, limit=1000)
                        if len(api_candles) > 0:
                            print("[ Fetched Start to End ]")
                            print(f"{api_candles[0]["open_time"].strftime('%Y-%m-%d %H:%M:%S')} -> {api_candles[-1]["open_time"].strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            # DB에 캔들 데이터 저장
                            insert_candles_to_db(api_candles)
                        # DB에 저장된 캔들 데이터에 API로 받은 캔들 데이터를 결합
                        final_candles = db_candles + api_candles
            # DB에 요청된 범위의 캔들 데이터가 없는 경우
            else:
                # 전체 데이터 요청
                api_candles = self.fetch_candles_from_api(symbol, interval, None, end_time_dt, limit=1000)
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
                    "volume": float(candle["volume"]),
                }

            normalized_candles = list(unique_candles.values())

            # open_time(time) 기준 오름차순 정렬
            normalized_candles.sort(key=lambda x: x["time"])

            #print(f"Normalized Candles Size : {len(normalized_candles)}")
            return normalized_candles
            
        except requests.exceptions.RequestException as e:
            Error("requests.exceptions.RequestException")
            print(e)
            return []
        except Exception as e:
            Error("Exception")
            traceback.print_exc()
            return []
    
    def fetch_candles_from_api(self, symbol: str, interval: str, start_time_dt: datetime, end_time_dt: datetime, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Binance API에서 캔들 데이터 조회
        캔들 데이터는 시간의 오름차순으로 정렬되어 있음
        (과거 데이터가 먼저)
        """
        try:
            """
            Info("[ Requested Candles ]")
            print(f"interval : {interval}")
            if start_time_dt != None:
                print(f"start_time_dt : {start_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"end_time_dt : {end_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"limit : {limit}")
            """

            limit = min(limit, 1000)
            limit = max(limit, 1)

            # 임의의 KST 시각을 KST 정각 시각으로 변환
            api_start_time_dt = None
            api_end_time_dt = None
            if interval == "1d":
                if start_time_dt != None:
                    api_start_time_dt = start_time_dt.replace(hour=0, minute=0, second=0, microsecond=0)

                api_end_time_dt = end_time_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            elif interval == "1h":
                if start_time_dt != None:
                    api_start_time_dt = start_time_dt.replace(minute=0, second=0, microsecond=0)

                api_end_time_dt = end_time_dt.replace(minute=0, second=0, microsecond=0)
            else:
                raise "Invalid interval."
            
            if api_start_time_dt != None:
                print(f"api_start_time_dt : {api_start_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"api_end_time_dt : {api_end_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")

            url = API_URL + "/api/v3/klines"
            # If timeZone provided, kline intervals are interpreted in that timezone instead of UTC.
            # Note that startTime and endTime are always interpreted in UTC, regardless of timeZone.
            # https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#klinecandlestick-data
            params = {
                "symbol": symbol,
                "interval": interval,
                "endTime": int(api_end_time_dt.timestamp() * 1000),
                "limit": limit,
                # 캔들을 KST 기준으로 계산
                "timeZone": "+09:00",
            }

            if api_start_time_dt != None:
                params["startTime"] = int(api_start_time_dt.timestamp() * 1000)
            
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            resp_json = resp.json()

            candles = []
            for row in resp_json:
                candles.append({
                    "broker_name": "Binance",
                    "symbol": symbol,
                    "interval": interval,
                    "open_time": datetime.fromtimestamp(row[0] / 1000.0),
                    "close_time": datetime.fromtimestamp(row[6] / 1000.0),
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5]),
                    "quote_volume": float(row[7]),
                    "trade_count": row[8],
                    "taker_buy_base_asset_volume": float(row[9]),
                    "taker_buy_quote_asset_volume": float(row[10]),
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
        Binance 주문 전송
        """
        return place_order(self.user_id, order)
    
    def cancel_order(self, order) -> List[Dict[str, Any]]:
        """
        Binance 주문 취소
        """
        return cancel_order(self.user_id, order)
    
    def cancel_all_orders(self) -> List[Dict[str, Any]]:
        """
        Binance 모든 주문 취소
        """
        return cancel_all_orders(None)

    def get_orders(self) -> List[NormalizedOrder]:
        """
        Binance 미체결 주문 목록
        """
        try:
            headers = {
                "X-MBX-APIKEY": get_key(self.user_id)["API"],
            }

            params = {}
            payload = get_signed_payload_post(self.user_id, params)

            url = API_URL + f"/api/v3/openOrders"
            resp = requests.get(url, headers=headers, params=payload, timeout=10)
            resp_json = resp.json()

            orders: List[NormalizedOrder] = []
            for order in resp_json:
                orders.append({
                    "order_id": order["orderId"],
                    # e.g. BTCUSDT
                    "symbol": order["symbol"],
                    # BUY or SELL
                    "side": str(order["side"]).lower(),
                    "price": order["price"],
                    "amount": order["origQty"],
                })

            return orders
            
        except requests.exceptions.RequestException as e:
            print("[ get_orders ]")
            print("requests.exceptions.RequestException:")
            print(e)
            return []
        except Exception as e:
            print("[ get_orders ]")
            print(e)
            import traceback
            traceback.print_exc()
            return []

    # https://developers.binance.com/docs/binance-spot-api-docs/user-data-stream#order-update
    async def subscribe_order_update_async(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        """
        Binance 실시간 주문 업데이트 구독
        -> 주문 접수/체결/취소 등
        """
        try:
            url = WS_URL
            async with websockets.connect(url, ping_interval=10.0, ping_timeout=10.0) as ws:
                params = {
                    "apiKey": get_key(self.user_id)["API"],
                }
                payload = get_signed_payload_ws(self.user_id, "session.logon", params)
                await ws.send(json.dumps(payload))
                resp = json.loads(await ws.recv())

                #print("[ session.logon ]")
                #print(resp)

                payload = {
                    "id": str(uuid.uuid4()),
                    "method": "userDataStream.subscribe",
                }
                await ws.send(json.dumps(payload))
                resp = json.loads(await ws.recv())

                #print("[ userDataStream.subscribe ]")
                #print(resp)

                while True:
                    try:
                        resp_json = json.loads(await ws.recv())
                        #pprint(resp_json)

                        if "event" in resp_json:
                            normalized_json = {}
                            # 주문 처리
                            if resp_json["event"]["e"] == "executionReport":
                                # 새 주문
                                if resp_json["event"]["x"] == "NEW":
                                    normalized_json = {
                                        # Order Status
                                        "order_status": "NEW",
                                        # Order ID
                                        "order_id": resp_json["event"]["i"],
                                        # Symbol
                                        "symbol": resp_json["event"]["s"],
                                        # Side
                                        # -> 대문자 S
                                        "side": resp_json["event"]["S"],
                                        # Order price
                                        "price": resp_json["event"]["p"],
                                        # Order quantity
                                        "quantity": resp_json["event"]["q"],
                                    }
                                # 주문 체결
                                elif resp_json["event"]["x"] == "TRADE":
                                    normalized_json = {
                                        # Order Status
                                        "order_status": "TRADE",
                                        # Order ID
                                        "order_id": resp_json["event"]["i"],
                                        # Symbol
                                        "symbol": resp_json["event"]["s"],
                                        # Side
                                        # -> 대문자 S
                                        "side": resp_json["event"]["S"],
                                        # Order price
                                        "price": resp_json["event"]["p"],
                                        # Order quantity
                                        "quantity": resp_json["event"]["q"],
                                    }
                                # 주문 취소
                                elif resp_json["event"]["x"] == "CANCELED":
                                    normalized_json = {
                                        # Order Status
                                        "order_status": "CANCELED",
                                        # Order ID
                                        "order_id": resp_json["event"]["i"],
                                        # Symbol
                                        "symbol": resp_json["event"]["s"],
                                        # Side
                                        # -> 대문자 S
                                        "side": resp_json["event"]["S"],
                                    }
                                await callback(normalized_json)
                        
                    except json.JSONDecodeError as e:
                        Error(f"JSON decode error: {e}")
                    except asyncio.CancelledErroras as e:
                        Error("asyncio.CancelledError")
                        print(e)
                        # 취소 신호 - 즉시 종료
                        raise
                    except Exception:
                        # 콜백 오류 (연결 끊김 등) - 조용히 종료
                        Error(f"Exception")
                        raise asyncio.CancelledError("Callback error")
        
        except asyncio.CancelledError:
            Info("Binance asyncio.CancelledError")
            pass
        except websockets.exceptions.ConnectionClosed:
            Info("Binance websockets.exceptions.ConnectionClosed")
            # Binance 연결 종료 - 로그 없음
            pass
        except Exception as e:
            Error(f"Binance WebSocket error: {e}")
            print(traceback.format_exc())
    
    async def subscribe_userdata_async(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        try:
            url = WS_URL
            async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                params = {
                    "apiKey": get_key(self.user_id)["API"],
                }
                payload = get_signed_payload_ws(self.user_id, "session.logon", params)
                await ws.send(json.dumps(payload))
                resp = json.loads(await ws.recv())

                print("[ session.logon ]")
                print(resp)

                payload = {
                    "id": str(uuid.uuid4()),
                    "method": "userDataStream.subscribe",
                }
                await ws.send(json.dumps(payload))
                resp = json.loads(await ws.recv())

                print("[ userDataStream.subscribe ]")
                print(resp)

                while True:
                    try:
                        resp_json = json.loads(await ws.recv())
                        await callback(resp_json)
                        
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                    except asyncio.CancelledError:
                        print("asyncio.CancelledError")
                        # 취소 신호 - 즉시 종료
                        raise
                    except Exception:
                        # 콜백 오류 (연결 끊김 등) - 조용히 종료
                        print(f"Exception")
                        raise asyncio.CancelledError("Callback error")
        
        except asyncio.CancelledError:
            # 정상적인 취소 - 로그 없음
            pass
        except websockets.exceptions.ConnectionClosed:
            # Binance 연결 종료 - 로그 없음
            pass
        except Exception as e:
            print(f"Binance WebSocket error: {e}")
            import traceback
            traceback.print_exc()
            print(traceback.format_exc())

    def get_assets(self) -> List[Dict[str, Any]]:
        try:
            headers = {
                "X-MBX-APIKEY": get_key(self.user_id)["API"],
            }

            params = {
                "recvWindow": "5000",
                "timestamp": str(int(time.time()) * 1000)
            }
            query_string = urlencode(params)
            signature = signing(query_string)

            url = API_URL + f"/sapi/v3/asset/getUserAsset?{query_string}&signature={signature}"
            resp = requests.post(url, headers=headers, data=params, timeout=10)
            resp_json = resp.json()

            assets = []
            for asset in resp_json:
                assets.append({
                    "display_name": "Spot " + asset["asset"],
                    "symbol": asset["asset"],
                    "amount": asset["free"],
                })

            params = {
                "recvWindow": "5000",
                "timestamp": str(int(time.time()) * 1000)
            }
            query_string = urlencode(params)
            signature = signing(query_string)

            url = API_URL + f"/sapi/v1/simple-earn/account?{query_string}&signature={signature}"
            resp = requests.get(url, headers=headers, timeout=10)
            resp_json = resp.json()

            assets.append({
                "display_name": "Simple Earn USDT",
                "symbol": "USDT",
                "amount": resp_json["totalAmountInUSDT"],
            })

            return assets
            
        except requests.exceptions.RequestException as e:
            print("[ get_assets ]")
            print("requests.exceptions.RequestException:")
            print(e)
            return []
        except Exception as e:
            print("[ get_assets ]")
            print(e)
            import traceback
            traceback.print_exc()
            return []

    def get_symbols(self) -> List[Dict[str, Any]]:
        try:
            url = API_URL + "/api/v3/exchangeInfo"
            params = {
                "permissions": "SPOT",
                "showPermissionSets": "false"
            }
            
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            
            resp_json = resp.json()
            
            symbols = []
            for symbol in resp_json["symbols"]:
                # 거래 가능한 pair만 처리
                if symbol["status"] == "TRADING":
                    # USDT가 quote asset인 경우만 가져오기
                    if symbol["quoteAsset"] == "USDT":
                        symbols.append({
                            "symbol": symbol["symbol"],
                            "display_name": f"{symbol['baseAsset']}/{symbol['quoteAsset']} ({symbol['symbol']})",
                        })
            return symbols
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching symbols from Binance: {e}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error in get_symbols: {e}")
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
    
    async def subscribe_orderbook_async(self, user_id: str, symbol: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        try:
            url = WSS_URL + "/ws"
            async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                payload = {
                    "method": "SUBSCRIBE",
                    "params": [
                        f"{symbol}@depth20@100ms"
                    ],
                    "id": 1
                }
                await ws.send(json.dumps(payload))
                #print(f"Subscribed to Binance {symbol} orderbook")

                while True:
                    try:
                        resp = json.loads(await ws.recv())
                        
                        if "bids" in resp and "asks" in resp:
                            normalized_data = {
                                "symbol": symbol,
                                "bids": [
                                    {"price": float(bid[0]), "quantity": float(bid[1])}
                                    for bid in resp['bids']
                                ],
                                "asks": [
                                    {"price": float(ask[0]), "quantity": float(ask[1])}
                                    for ask in resp['asks']
                                ],
                            }
                            
                            # 콜백 호출 - 예외 발생 시 루프 종료
                            await callback(normalized_data)
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                    except asyncio.CancelledError:
                        # 취소 신호 - 즉시 종료
                        raise
                    except Exception:
                        # 콜백 오류 (연결 끊김 등) - 조용히 종료
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

    async def subscribe_trade_price_async(self, user_id: str, symbol: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        url = WSS_URL + "/ws"
        
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                payload = {
                    "method": "SUBSCRIBE",
                    "params": [
                        f"{symbol}@trade"
                    ],
                    "id": 1
                }
                await ws.send(json.dumps(payload))
                #print(f"Subscribed to Binance {symbol} trade")

                while True:
                    try:
                        resp = json.loads(await ws.recv())
                        
                        if "e" in resp and resp["e"] == "trade":
                            # 시간 포맷팅 (HH:MM:SS)
                            timestamp_ms = resp.get("T", 0)
                            time_str = ""
                            if timestamp_ms:
                                from datetime import datetime
                                dt = datetime.fromtimestamp(timestamp_ms / 1000)
                                time_str = dt.strftime("%H:%M:%S")
                            
                            normalized_data = {
                                "symbol": resp["s"],
                                "price": resp["p"],
                                "quantity": resp["q"],
                                "time": time_str,
                                "isBuyerMaker": resp["m"],
                                "timestamp": timestamp_ms,
                            }
                            
                            # 콜백 호출 - 예외 발생 시 루프 종료
                            await callback(normalized_data)
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                    except asyncio.CancelledError:
                        # 취소 신호 - 즉시 종료
                        raise
                    except Exception:
                        # 콜백 오류 (연결 끊김 등) - 조용히 종료
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