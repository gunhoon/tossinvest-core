from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class Currency(str, Enum):
    KRW = "KRW"
    USD = "USD"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PENDING_CANCEL = "PENDING_CANCEL"
    PENDING_REPLACE = "PENDING_REPLACE"
    PARTIAL_FILLED = "PARTIAL_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    CANCEL_REJECTED = "CANCEL_REJECTED"
    REPLACE_REJECTED = "REPLACE_REJECTED"
    REPLACED = "REPLACED"


class MarketCountry(str, Enum):
    KR = "KR"
    US = "US"


class StockStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    DELISTED = "DELISTED"


class Account(TypedDict):
    accountSeq: int
    accountNo: str
    name: str
    type: str


class Price(TypedDict):
    krw: str
    usd: Optional[str]


class OverviewValue(TypedDict):
    total: Price
    kr: Price
    us: Price


class HoldingsItem(TypedDict):
    symbol: str
    name: str
    marketCountry: str
    currency: str
    quantity: str
    lastPrice: str
    averagePurchasePrice: str
    marketValue: Dict[str, Any]
    profitLoss: Dict[str, Any]
    dailyProfitLoss: Dict[str, Any]
    cost: Dict[str, Any]


class HoldingsOverview(TypedDict):
    totalPurchaseAmount: Price
    marketValue: OverviewValue
    profitLoss: OverviewValue
    dailyProfitLoss: OverviewValue
    items: List[HoldingsItem]


class Candle(TypedDict):
    timestamp: str
    openPrice: str
    highPrice: str
    lowPrice: str
    closePrice: str
    volume: str
    currency: str


class StockInfo(TypedDict):
    symbol: str
    name: str
    englishName: Optional[str]
    marketCountry: str
    marketDetail: str
    type: str
    isCommonShare: bool
    status: str
    currency: str
    listDate: Optional[str]
    delistDate: Optional[str]
    sharesOutstanding: str
    leverageFactor: Optional[str]
    koreanMarketDetail: Optional[Dict[str, Any]]


class OrderExecution(TypedDict):
    filledQuantity: str
    averageFilledPrice: Optional[str]
    filledAmount: Optional[str]
    commission: Optional[str]
    tax: Optional[str]
    filledAt: Optional[str]
    settlementDate: Optional[str]


class Order(TypedDict):
    orderId: str
    clientOrderId: Optional[str]
    symbol: str
    side: str
    orderType: str
    timeInForce: str
    status: str
    price: Optional[str]
    quantity: str
    orderAmount: Optional[str]
    currency: str
    orderedAt: str
    canceledAt: Optional[str]
    execution: OrderExecution
