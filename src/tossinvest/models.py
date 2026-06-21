from enum import Enum
from typing import Any, Dict, List, Optional, Union, TypedDict


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


class RateChangeType(str, Enum):
    UP = "UP"
    EQUAL = "EQUAL"
    DOWN = "DOWN"


class WarningType(str, Enum):
    LIQUIDATION_TRADING = "LIQUIDATION_TRADING"
    OVERHEATED = "OVERHEATED"
    INVESTMENT_WARNING = "INVESTMENT_WARNING"
    INVESTMENT_RISK = "INVESTMENT_RISK"
    VI_STATIC_AND_DYNAMIC = "VI_STATIC_AND_DYNAMIC"
    VI_STATIC = "VI_STATIC"
    VI_DYNAMIC = "VI_DYNAMIC"
    STOCK_WARRANTS = "STOCK_WARRANTS"


# ==========================================
# AUTH SCHEMAS
# ==========================================

class OAuth2TokenResponse(TypedDict):
    access_token: str
    token_type: str
    expires_in: int


# ==========================================
# MARKET DATA SCHEMAS
# ==========================================

class PriceResponse(TypedDict):
    symbol: str
    timestamp: Optional[str]
    lastPrice: str
    currency: Currency


class OrderbookEntry(TypedDict):
    price: str
    volume: str


class OrderbookResponse(TypedDict):
    timestamp: Optional[str]
    currency: Currency
    asks: List[OrderbookEntry]
    bids: List[OrderbookEntry]


class Candle(TypedDict):
    timestamp: str
    openPrice: str
    highPrice: str
    lowPrice: str
    closePrice: str
    volume: str
    currency: Currency


class CandlePageResponse(TypedDict):
    candles: List[Candle]
    nextBefore: Optional[str]


class PriceLimitResponse(TypedDict):
    timestamp: str
    upperLimitPrice: Optional[str]
    lowerLimitPrice: Optional[str]
    currency: Currency


class Trade(TypedDict):
    price: str
    volume: str
    timestamp: str
    currency: Currency


# ==========================================
# STOCK / MARKET INFO SCHEMAS
# ==========================================

class StockInfo(TypedDict):
    symbol: str
    name: str
    englishName: str
    isinCode: str
    market: str
    securityType: str
    isCommonShare: bool
    status: StockStatus
    currency: Currency
    listDate: Optional[str]
    delistDate: Optional[str]
    sharesOutstanding: str
    leverageFactor: Optional[str]
    koreanMarketDetail: Optional[Dict[str, Any]]


class StockWarning(TypedDict):
    warningType: WarningType
    exchange: Optional[str]
    startDate: Optional[str]
    endDate: Optional[str]


class ExchangeRateResponse(TypedDict):
    baseCurrency: Currency
    quoteCurrency: Currency
    rate: str
    midRate: str
    basisPoint: str
    rateChangeType: RateChangeType
    validFrom: str
    validUntil: str


class PreMarketSession(TypedDict):
    startTime: str
    singlePriceAuctionStartTime: Optional[str]
    endTime: str


class RegularMarketSession(TypedDict):
    startTime: str
    singlePriceAuctionStartTime: Optional[str]
    endTime: str


class AfterMarketSession(TypedDict):
    startTime: str
    singlePriceAuctionEndTime: Optional[str]
    endTime: str


class IntegratedHour(TypedDict):
    preMarket: Optional[PreMarketSession]
    regularMarket: Optional[RegularMarketSession]
    afterMarket: Optional[AfterMarketSession]


class KrMarketDay(TypedDict):
    date: str
    integrated: Optional[IntegratedHour]


class KrMarketCalendarResponse(TypedDict):
    today: KrMarketDay
    previousBusinessDay: KrMarketDay
    nextBusinessDay: KrMarketDay


class UsDayMarketSession(TypedDict):
    startTime: str
    endTime: str


class UsPreMarketSession(TypedDict):
    startTime: str
    endTime: str


class UsRegularMarketSession(TypedDict):
    startTime: str
    endTime: str


class UsAfterMarketSession(TypedDict):
    startTime: str
    endTime: str


class UsMarketDay(TypedDict):
    date: str
    dayMarket: Optional[UsDayMarketSession]
    preMarket: Optional[UsPreMarketSession]
    regularMarket: Optional[UsRegularMarketSession]
    afterMarket: Optional[UsAfterMarketSession]


class UsMarketCalendarResponse(TypedDict):
    today: UsMarketDay
    previousBusinessDay: UsMarketDay
    nextBusinessDay: UsMarketDay


# ==========================================
# ACCOUNT SCHEMAS
# ==========================================

class Account(TypedDict):
    accountNo: str
    accountSeq: int
    accountType: str


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
    marketCountry: MarketCountry
    currency: Currency
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


# ==========================================
# ORDER SCHEMAS
# ==========================================

class OrderResponse(TypedDict):
    orderId: str
    clientOrderId: Optional[str]


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
    status: OrderStatus
    price: Optional[str]
    quantity: str
    orderAmount: Optional[str]
    currency: Currency
    orderedAt: str
    canceledAt: Optional[str]
    execution: OrderExecution


class PaginatedOrderResponse(TypedDict):
    orders: List[Order]
    nextCursor: Optional[str]
    hasNext: bool


class BuyingPowerResponse(TypedDict):
    currency: Currency
    cashBuyingPower: str


class SellableQuantityResponse(TypedDict):
    sellableQuantity: str


class Commission(TypedDict):
    marketCountry: MarketCountry
    commissionRate: str
    startDate: Optional[str]
    endDate: Optional[str]
