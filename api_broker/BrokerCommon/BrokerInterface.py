from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BrokerInterface(ABC):
    @abstractmethod
    def ping_http(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def ping_ws(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_account_assets(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def get_realtime_orderbook_price(self, symbol: str) -> Dict[str, Any]:
        pass