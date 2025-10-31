from ..BrokerCommon.BrokerInterface import BrokerInterface
from .price import get_realtime_orderbook_price, get_realtime_trade_price
from .constants import WSS_URL
from typing import List, Dict, Any, Callable, Awaitable
import websockets
import json
import traceback
import asyncio

# Endpoint 마다 rate limit 관리 코드 추가하기!!
# HTTP 429 return code is used when breaking a request rate limit.
# HTTP 418 return code is used when an IP has been auto-banned for continuing to send requests after receiving 429 codes.
# Ping 프레임 수신시 pong 프레임으로 응답 필요(Ping 프레임과 같은 내용으로)
# -> 라이브러리에서 자동으로 처리되는건가?

class BinanceBroker(BrokerInterface):
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
    
    def get_candle_data(self, crypto_pair: str, )
    
    async def subscribe_orderbook_async(self, crypto_pair: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        try:
            url = WSS_URL + "/ws"
            async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                payload = {
                    "method": "SUBSCRIBE",
                    "params": [
                        f"{crypto_pair}@depth20@100ms"
                    ],
                    "id": 1
                }
                await ws.send(json.dumps(payload))
                print(f"✅ Subscribed to Binance {crypto_pair} orderbook")

                while True:
                    try:
                        resp = json.loads(await ws.recv())
                        
                        if "bids" in resp and "asks" in resp:
                            normalized_data = {
                                "symbol": crypto_pair,
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

    async def subscribe_trade_price_async(self, crypto_pair: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        url = WSS_URL + "/ws"
        
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                payload = {
                    "method": "SUBSCRIBE",
                    "params": [
                        f"{crypto_pair}@trade"
                    ],
                    "id": 1
                }
                await ws.send(json.dumps(payload))
                print(f"✅ Subscribed to Binance {crypto_pair} trade")

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