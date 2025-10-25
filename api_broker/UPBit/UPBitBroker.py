from BrokerCommon import BrokerInterface
from .account import get_account_assets as _get_account_assets
from typing import List, Dict, Any

class UpbitBroker(BrokerInterface):
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.ws = None
    
    def get_account_assets(self) -> List[Dict[str, Any]]:
        """업비트 자산 조회"""
        assets = _get_account_assets()
        return self._normalize_assets(assets)
    
    def get_realtime_price(self, symbol: str) -> Dict[str, Any]:
        """업비트 실시간 시세"""
        pass
        #return _get_realtime_price(symbol)
    
    def _normalize_assets(self, raw_assets: List[Dict]) -> List[Dict]:
        """업비트 응답을 표준 포맷으로 변환"""
        return [
            {
                'symbol': asset['currency'],
                'balance': float(asset['balance']),
                'available': float(asset['balance']) - float(asset.get('locked', 0)),
                'locked': float(asset.get('locked', 0)),
                'avg_buy_price': float(asset.get('avg_buy_price', 0)),
                'type': 'crypto'
            }
            for asset in raw_assets
        ]