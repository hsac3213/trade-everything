from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BrokerInterface(ABC):    
    @abstractmethod
    def get_account_assets(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def get_realtime_price(self, symbol: str) -> Dict[str, Any]:
        pass