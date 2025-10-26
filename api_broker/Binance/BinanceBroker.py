from ..BrokerCommon.BrokerInterface import BrokerInterface
from .price import get_realtime_orderbook_price, get_realtime_trade_price
from typing import List, Dict, Any, Callable
import websocket
import json
import threading
import time

# Endpoint 마다 rate limit 관리 코드 추가하기!!
# HTTP 429 return code is used when breaking a request rate limit.
# HTTP 418 return code is used when an IP has been auto-banned for continuing to send requests after receiving 429 codes.
class BinanceBroker(BrokerInterface):
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.ws = None
        self.ws_thread = None
        self.orderbook_callback = None
    
    def get_account_assets(self) -> List[Dict[str, Any]]:
        """바이낸스 자산 조회"""
        # TODO: 실제 바이낸스 API 호출 구현
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
        """바이낸스 주문"""
        # TODO: 실제 바이낸스 API 호출 구현
        return {
            'order_id': '12345',
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'status': 'pending'
        }
    
    def subscribe_orderbook(self, symbol: str, callback: Callable):
        """
        바이낸스 실시간 호가 구독
        
        Args:
            symbol: 심볼 (예: 'btcusdt')
            callback: 호가 데이터를 받을 콜백 함수
        """
        self.orderbook_callback = callback
        
        # WebSocket URL (Depth Stream - 100ms마다 업데이트)
        ws_url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@depth20@100ms"
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                
                # 바이낸스 응답 포맷을 표준 포맷으로 변환
                normalized_data = {
                    'symbol': symbol.upper(),
                    'bids': [
                        {'price': float(bid[0]), 'size': float(bid[1])}
                        for bid in data.get('bids', [])[:20]  # 상위 20개만
                    ],
                    'asks': [
                        {'price': float(ask[0]), 'size': float(ask[1])}
                        for ask in data.get('asks', [])[:20]  # 상위 20개만
                    ],
                    'timestamp': data.get('E', int(time.time() * 1000))
                }
                
                if self.orderbook_callback:
                    self.orderbook_callback(normalized_data)
                    
            except Exception as e:
                print(f"❌ Error processing orderbook data: {e}")
        
        def on_error(ws, error):
            print(f"❌ WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print(f"🔌 WebSocket closed: {close_status_code}")
        
        def on_open(ws):
            print(f"✅ WebSocket connected to Binance {symbol} orderbook")
        
        # WebSocket 실행
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        # 별도 스레드에서 실행
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()
    
    def unsubscribe_orderbook(self):
        """호가 구독 해제"""
        if self.ws:
            self.ws.close()
            self.ws = None
        self.orderbook_callback = None