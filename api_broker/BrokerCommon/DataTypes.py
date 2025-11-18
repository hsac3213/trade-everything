"""
주문, 자산, 거래 등에 대한 정규화된 데이터 형식 정의
"""
from typing import TypedDict, Literal

class NormalizedAsset(TypedDict):
    display_name: str
    amount: str

class NormalizedTrade(TypedDict):
    symbol: str
    price: str
    quantity: str
    time: str
    isBuyerMaker: bool
    timestamp: int

class NormalizedOrder(TypedDict):
    order_id: str
    symbol: str
    side: Literal['buy', 'sell']
    price: str
    amount: str

class NormalizedPlaceOrder(TypedDict):
    order_id: str
    symbol: str
    side: Literal['buy', 'sell']
    price: str
    amount: str

class NormalizedCancelOrder(TypedDict):
    symbol: str
    order_id: str