from ..BrokerCommon.BrokerInterface import BrokerInterface
from .price import get_realtime_orderbook_price, get_realtime_trade_price
from .constants import WSS_URL
from typing import List, Dict, Any, Callable, Awaitable
import websockets
import json
import traceback

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
    
    async def subscribe_orderbook_async(self, crypto_pair: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        url = WSS_URL + "/ws"
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                payload = {
                    "method": "SUBSCRIBE",
                    "params": [
                        f"{crypto_pair}@depth20@100ms"
                    ],
                    "id": 1
                }
                await ws.send(json.dumps(payload))

                while True:
                    try:
                        resp = json.loads(await ws.recv())
                        
                        if "bids" not in resp:
                            print(resp)
                        else:
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
                            await callback(normalized_data)
                        
                    except json.JSONDecodeError as e:
                        print("[ subscribe_orderbook_async ]")
                        print(f"JSONDecodeError: {e}")
                    except Exception as e:
                        print("[ subscribe_orderbook_async ]")
                        print(f"Exception: {e}")
                        print(traceback.format_exc())
        
        except websockets.exceptions.ConnectionClosed as e:
            print("[ subscribe_orderbook_async ]")
            print(f"ConnectionClosed: {e}")
        except Exception as e:
            print("[ subscribe_orderbook_async ]")
            print(f"Exception: {e}")
            print(traceback.format_exc())