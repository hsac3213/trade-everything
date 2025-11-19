from typing import Dict, Type, List
from .BrokerInterface import BrokerInterface
from ..Binance.BinanceBroker import BinanceBroker
from ..KIS.KISBroker import KISBroker

class BrokerFactory:    
    _brokers: Dict[str, Type[BrokerInterface]] = {
        "Binance": BinanceBroker,
        "KIS": KISBroker,
    }
    
    @classmethod
    def create_broker(cls, broker_name: str, user_id: str = None) -> BrokerInterface:
        broker_class = cls._brokers.get(broker_name)
        if not broker_class:
            raise ValueError(f"Unsupported broker: {broker_name}")
        
        return broker_class(user_id=user_id)
    
    @classmethod
    def register_broker(cls, name: str, broker_class: Type[BrokerInterface]):
        """새로운 브로커 등록 (확장성)"""
        cls._brokers[name] = broker_class
    
    @classmethod
    def get_available_brokers(cls) -> List[str]:
        """사용 가능한 브로커 목록"""
        return list(cls._brokers.keys())


# 테스트 코드
if __name__ == "__main__":
    print("🔧 Testing BrokerFactory...")
    print(f"Available brokers: {BrokerFactory.get_available_brokers()}")
    
    try:
        binance = BrokerFactory.create_broker('Binance')
        print(f"✅ Binance broker created: {type(binance).__name__}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()