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
    # 클래스 레벨 공유 WebSocket 관리 (모든 인스턴스가 공유)
    _shared_ws = None
    _shared_ws_task = None
    _shared_is_connected = False
    _shared_lock = asyncio.Lock()
    _shared_ticker_symbol = None
    _shared_orderbook_callbacks = []  # 여러 구독자 지원
    _shared_trade_callbacks = []      # 여러 구독자 지원
    
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.api_key = api_key
        self.secret_key = secret_key

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
    
    async def _ensure_connection(self, ticker_symbol: str):
        """WebSocket 연결 보장 (없으면 생성)"""
        async with KISBroker._shared_lock:
            if KISBroker._shared_is_connected and KISBroker._shared_ticker_symbol == ticker_symbol:
                return
            
            # 기존 연결 정리
            if KISBroker._shared_ws_task:
                KISBroker._shared_ws_task.cancel()
                try:
                    await KISBroker._shared_ws_task
                except asyncio.CancelledError:
                    pass
            
            # 새 연결 시작
            KISBroker._shared_ticker_symbol = ticker_symbol
            KISBroker._shared_ws_task = asyncio.create_task(self._ws_loop(ticker_symbol))
            
            # 연결 대기
            for _ in range(50):  # 5초 대기
                if KISBroker._shared_is_connected:
                    return
                await asyncio.sleep(0.1)
            
            raise Exception("WebSocket connection timeout")
    
    async def _ws_loop(self, ticker_symbol: str):
        """공유 WebSocket 루프"""
        try:
            url = WS_URL
            async with websockets.connect(url, ping_interval=30) as ws:
                KISBroker._shared_ws = ws
                
                # 호가 구독 (HDFSASP0)
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
                            "tr_key": ticker_symbol,
                        }
                    }
                }
                await ws.send(json.dumps(payload))
                
                # 체결가 구독 (HDFSCNT0)
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
                            "tr_key": ticker_symbol,
                        }
                    }
                }
                await ws.send(json.dumps(payload))
                
                KISBroker._shared_is_connected = True
                print(f"✅ KIS WebSocket connected: {ticker_symbol}")
                
                while True:
                    try:
                        resp = await ws.recv()
                        await self._handle_message(resp, ticker_symbol)
                        
                    except asyncio.CancelledError:
                        raise
                    except websockets.exceptions.ConnectionClosedError:
                        # WebSocket 연결 끊김 - 루프 종료
                        print(f"⚠️ KIS WebSocket connection closed: {ticker_symbol}")
                        break
                    except Exception as e:
                        print(f"❌ Error in message handler: {e}")
                        import traceback
                        traceback.print_exc()
                        
        except asyncio.CancelledError:
            pass
        except websockets.exceptions.ConnectionClosed:
            pass
        except websockets.exceptions.ConnectionClosedError:
            pass
        except Exception as e:
            print(f"❌ KIS WebSocket error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            KISBroker._shared_is_connected = False
            KISBroker._shared_ws = None
            print(f"🔌 KIS WebSocket disconnected: {ticker_symbol}")
    
    async def _handle_message(self, resp: str, ticker_symbol: str):
        """메시지 타입별 라우팅"""
        # PING-PONG 처리
        if resp[0] not in ["0", "1"]:
            try:
                json_data = json.loads(resp)
                print(json_data)
                if json_data.get("header", {}).get("tr_id") == "PINGPONG":
                    await KISBroker._shared_ws.pong(resp)
                    print("🏓 Pong!")
            except json.JSONDecodeError:
                print("JSONDecodeError")
                pass
            return
        
        # 데이터 메시지 - tr_id로 구분
        meta_data = resp.split("|")
        if len(meta_data) < 2:
            return
        
        tr_id = meta_data[1]
        
        # 호가 데이터 (HDFSASP0) - 모든 구독자에게 전달
        if tr_id == "HDFSASP0" and KISBroker._shared_orderbook_callbacks:
            await self._handle_orderbook(resp, ticker_symbol)
        
        # 체결가 데이터 (HDFSCNT0) - 모든 구독자에게 전달
        elif tr_id == "HDFSCNT0" and KISBroker._shared_trade_callbacks:
            await self._handle_trade(resp, ticker_symbol)
    
    async def _handle_orderbook(self, resp: str, ticker_symbol: str):
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
                "symbol": ticker_symbol,
                "bids": [
                    {"price": float(resp_dict["매수호가1"]), "quantity": float(resp_dict["매수잔량1"])}
                ],
                "asks": [
                    {"price": float(resp_dict["매도호가1"]), "quantity": float(resp_dict["매도잔량1"])}
                ],
            }
            print(normalized_data["asks"])
            
            # 모든 호가 구독자에게 전달
            for callback in KISBroker._shared_orderbook_callbacks:
                try:
                    await callback(normalized_data)
                except Exception as e:
                    print(f"❌ Error in orderbook callback: {e}")
            
        except Exception as e:
            print(f"❌ Error parsing orderbook: {e}")
    
    async def _handle_trade(self, resp: str, ticker_symbol: str):
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
                "symbol": resp_dict["종목코드"],
                "price": float(resp_dict["현재가"]) if resp_dict["현재가"] else 0.0,
                "quantity": float(resp_dict["체결량"]) if resp_dict["체결량"] else 0.0,
                "time": resp_dict["한국시간"],
                "isBuyerMaker": True,
                "timestamp": int(asyncio.get_event_loop().time() * 1000),
            }
            
            # 모든 체결가 구독자에게 전달
            for callback in KISBroker._shared_trade_callbacks:
                try:
                    await callback(normalized_data)
                except Exception as e:
                    print(f"❌ Error in trade callback: {e}")
            
        except Exception as e:
            print(f"❌ Error parsing trade: {e}")
    
    async def subscribe_orderbook_async(self, ticker_symbol: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        """호가 구독 (공유 WebSocket 사용)"""
        try:
            # 콜백 등록
            KISBroker._shared_orderbook_callbacks.append(callback)
            await self._ensure_connection("DNASNVDA")
            
            # 연결이 끊길 때까지 대기
            while KISBroker._shared_is_connected:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            pass
        finally:
            # 콜백 제거
            if callback in KISBroker._shared_orderbook_callbacks:
                KISBroker._shared_orderbook_callbacks.remove(callback)

    async def subscribe_trade_price_async(self, ticker_symbol: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        """체결가 구독 (공유 WebSocket 사용)"""
        try:
            # 콜백 등록
            KISBroker._shared_trade_callbacks.append(callback)
            await self._ensure_connection("DNASNVDA")
            
            # 연결이 끊길 때까지 대기
            while KISBroker._shared_is_connected:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            pass
        finally:
            # 콜백 제거
            if callback in KISBroker._shared_trade_callbacks:
                KISBroker._shared_trade_callbacks.remove(callback)