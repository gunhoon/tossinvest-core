from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class OAuth2TokenResponse:
    access_token: str
    token_type: str
    expires_in: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OAuth2TokenResponse":
        return cls(
            access_token=data.get("access_token"),
            token_type=data.get("token_type"),
            expires_in=int(data.get("expires_in", 0)),
        )


@dataclass
class Account:
    accountNo: str
    accountSeq: int
    accountType: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Account":
        return cls(
            accountNo=data.get("accountNo"),
            accountSeq=int(data.get("accountSeq")),
            accountType=data.get("accountType"),
        )


@dataclass
class Price:
    krw: float
    usd: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional["Price"]:
        if data is None:
            return None
        return cls(
            krw=float(data.get("krw", 0)),
            usd=float(data.get("usd")) if data.get("usd") is not None else None,
        )


@dataclass
class OverviewMarketValue:
    krw: float
    usd: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional["OverviewMarketValue"]:
        if data is None:
            return None
        return cls(
            krw=float(data.get("krw", 0)),
            usd=float(data.get("usd")) if data.get("usd") is not None else None,
        )


@dataclass
class OverviewProfitLoss:
    krw: float
    usd: Optional[float] = None
    rate: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional["OverviewProfitLoss"]:
        if data is None:
            return None
        return cls(
            krw=float(data.get("krw", 0)),
            usd=float(data.get("usd")) if data.get("usd") is not None else None,
            rate=float(data.get("rate", 0)),
        )


@dataclass
class OverviewDailyProfitLoss:
    krw: float
    usd: Optional[float] = None
    rate: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional["OverviewDailyProfitLoss"]:
        if data is None:
            return None
        return cls(
            krw=float(data.get("krw", 0)),
            usd=float(data.get("usd")) if data.get("usd") is not None else None,
            rate=float(data.get("rate", 0)),
        )


@dataclass
class HoldingsItem:
    symbol: str
    name: str
    marketCountry: str
    currency: str
    quantity: float
    lastPrice: float
    averagePurchasePrice: float
    marketValue: Dict[str, Any] = field(default_factory=dict)
    profitLoss: Dict[str, Any] = field(default_factory=dict)
    dailyProfitLoss: Dict[str, Any] = field(default_factory=dict)
    cost: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HoldingsItem":
        return cls(
            symbol=data.get("symbol"),
            name=data.get("name"),
            marketCountry=data.get("marketCountry"),
            currency=data.get("currency"),
            quantity=float(data.get("quantity", 0)),
            lastPrice=float(data.get("lastPrice", 0)),
            averagePurchasePrice=float(data.get("averagePurchasePrice", 0)),
            marketValue=data.get("marketValue", {}),
            profitLoss=data.get("profitLoss", {}),
            dailyProfitLoss=data.get("dailyProfitLoss", {}),
            cost=data.get("cost", {}),
        )


@dataclass
class HoldingsOverview:
    totalPurchaseAmount: Optional[Price]
    marketValue: Optional[OverviewMarketValue]
    profitLoss: Optional[OverviewProfitLoss]
    dailyProfitLoss: Optional[OverviewDailyProfitLoss]
    items: List[HoldingsItem]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HoldingsOverview":
        return cls(
            totalPurchaseAmount=Price.from_dict(data.get("totalPurchaseAmount")),
            marketValue=OverviewMarketValue.from_dict(data.get("marketValue")),
            profitLoss=OverviewProfitLoss.from_dict(data.get("profitLoss")),
            dailyProfitLoss=OverviewDailyProfitLoss.from_dict(data.get("dailyProfitLoss")),
            items=[HoldingsItem.from_dict(item) for item in data.get("items", [])],
        )


@dataclass
class PriceResponse:
    symbol: str
    lastPrice: float
    currency: str
    timestamp: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PriceResponse":
        return cls(
            symbol=data.get("symbol"),
            lastPrice=float(data.get("lastPrice", 0)),
            currency=data.get("currency"),
            timestamp=data.get("timestamp"),
        )


@dataclass
class OrderbookEntry:
    price: float
    volume: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderbookEntry":
        return cls(
            price=float(data.get("price", 0)),
            volume=float(data.get("volume", 0)),
        )


@dataclass
class OrderbookResponse:
    currency: str
    asks: List[OrderbookEntry]
    bids: List[OrderbookEntry]
    timestamp: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderbookResponse":
        return cls(
            currency=data.get("currency"),
            asks=[OrderbookEntry.from_dict(item) for item in data.get("asks", [])],
            bids=[OrderbookEntry.from_dict(item) for item in data.get("bids", [])],
            timestamp=data.get("timestamp"),
        )


@dataclass
class Candle:
    timestamp: str
    openPrice: float
    highPrice: float
    lowPrice: float
    closePrice: float
    volume: float
    currency: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Candle":
        return cls(
            timestamp=data.get("timestamp"),
            openPrice=float(data.get("openPrice", 0)),
            highPrice=float(data.get("highPrice", 0)),
            lowPrice=float(data.get("lowPrice", 0)),
            closePrice=float(data.get("closePrice", 0)),
            volume=float(data.get("volume", 0)),
            currency=data.get("currency"),
        )


@dataclass
class CandlePageResponse:
    candles: List[Candle]
    nextBefore: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CandlePageResponse":
        return cls(
            candles=[Candle.from_dict(item) for item in data.get("candles", [])],
            nextBefore=data.get("nextBefore"),
        )


@dataclass
class StockInfo:
    symbol: str
    name: str
    englishName: str
    isinCode: str
    market: str
    securityType: str
    isCommonShare: bool
    status: str
    currency: str
    sharesOutstanding: float
    listDate: Optional[str] = None
    delistDate: Optional[str] = None
    leverageFactor: Optional[float] = None
    koreanMarketDetail: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StockInfo":
        return cls(
            symbol=data.get("symbol"),
            name=data.get("name"),
            englishName=data.get("englishName"),
            isinCode=data.get("isinCode"),
            market=data.get("market"),
            securityType=data.get("securityType"),
            isCommonShare=data.get("isCommonShare"),
            status=data.get("status"),
            currency=data.get("currency"),
            sharesOutstanding=float(data.get("sharesOutstanding", 0)),
            listDate=data.get("listDate"),
            delistDate=data.get("delistDate"),
            leverageFactor=float(data.get("leverageFactor")) if data.get("leverageFactor") is not None else None,
            koreanMarketDetail=data.get("koreanMarketDetail"),
        )


@dataclass
class StockWarning:
    warningType: str
    startDate: str
    endDate: Optional[str] = None
    exchange: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StockWarning":
        return cls(
            warningType=data.get("warningType"),
            startDate=data.get("startDate"),
            endDate=data.get("endDate"),
            exchange=data.get("exchange"),
        )


@dataclass
class OrderExecution:
    filledQuantity: float
    averageFilledPrice: Optional[float] = None
    fees: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderExecution":
        return cls(
            filledQuantity=float(data.get("filledQuantity", 0)),
            averageFilledPrice=float(data.get("averageFilledPrice")) if data.get("averageFilledPrice") is not None else None,
            fees=float(data.get("fees")) if data.get("fees") is not None else None,
        )


@dataclass
class Order:
    orderId: str
    symbol: str
    side: str
    orderType: str
    timeInForce: str
    status: str
    quantity: float
    currency: str
    orderedAt: str
    execution: OrderExecution
    price: Optional[float] = None
    orderAmount: Optional[float] = None
    canceledAt: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        return cls(
            orderId=data.get("orderId"),
            symbol=data.get("symbol"),
            side=data.get("side"),
            orderType=data.get("orderType"),
            timeInForce=data.get("timeInForce"),
            status=data.get("status"),
            quantity=float(data.get("quantity", 0)),
            currency=data.get("currency"),
            orderedAt=data.get("orderedAt"),
            execution=OrderExecution.from_dict(data.get("execution", {})),
            price=float(data.get("price")) if data.get("price") is not None else None,
            orderAmount=float(data.get("orderAmount")) if data.get("orderAmount") is not None else None,
            canceledAt=data.get("canceledAt"),
        )


@dataclass
class OrderOperationResponse:
    orderId: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderOperationResponse":
        return cls(
            orderId=data.get("orderId"),
        )


@dataclass
class PaginatedOrderResponse:
    orders: List[Order]
    hasNext: bool
    nextCursor: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaginatedOrderResponse":
        return cls(
            orders=[Order.from_dict(item) for item in data.get("orders", [])],
            hasNext=bool(data.get("hasNext", False)),
            nextCursor=data.get("nextCursor"),
        )

