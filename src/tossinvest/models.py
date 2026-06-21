from dataclasses import dataclass, fields, is_dataclass, MISSING
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

T = TypeVar("T")


def _to_snake_case(s: str) -> str:
    """Converts camelCase to snake_case, handling boundaries cleanly."""
    res = []
    for i, char in enumerate(s):
        if char.isupper():
            if i > 0 and s[i - 1] != "_" and not s[i - 1].isupper():
                res.append("_")
            elif i > 0 and i < len(s) - 1 and s[i + 1].islower() and s[i - 1].isupper():
                res.append("_")
            res.append(char.lower())
        else:
            res.append(char)
    return "".join(res)


def from_dict(cls: Type[T], data: Any) -> T:
    """Recursively constructs a dataclass from a dictionary, mapping camelCase keys to snake_case."""
    if data is None:
        return None
    if not is_dataclass(cls):
        return data

    field_types = {f.name: f.type for f in fields(cls)}
    field_defaults = {f.name: f.default for f in fields(cls) if f.default is not MISSING}

    mapped_data = {}
    for k, v in data.items():
        snake_k = _to_snake_case(k)
        if snake_k in field_types:
            mapped_data[snake_k] = v

    args = {}
    for f in fields(cls):
        name = f.name
        val = mapped_data.get(name)

        if name not in mapped_data:
            # Check if there is a default value
            if f.default is not MISSING:
                args[name] = f.default
                continue
            # Check for factory
            if f.default_factory is not MISSING:
                args[name] = f.default_factory()
                continue
            # Handle Optional typing by defaulting to None
            origin = get_origin(f.type)
            if origin is Union and type(None) in get_args(f.type):
                args[name] = None
                continue
            # Default to None if not specified and not required
            args[name] = None
            continue

        ftype = f.type
        origin = get_origin(ftype)
        if origin is Union:
            args_types = [t for t in get_args(ftype) if t is not type(None)]
            if args_types:
                ftype = args_types[0]
                origin = get_origin(ftype)

        if origin is list or ftype is list:
            inner_args = get_args(f.type)
            if inner_args:
                inner_type = inner_args[0]
                if is_dataclass(inner_type):
                    args[name] = [from_dict(inner_type, item) for item in val] if isinstance(val, list) else val
                    continue
            args[name] = val
        elif is_dataclass(ftype):
            args[name] = from_dict(ftype, val)
        else:
            args[name] = val

    return cls(**args)


# Standard library helpers for get_origin and get_args to work with older python if needed
try:
    from typing import get_args, get_origin
except ImportError:
    def get_origin(tp):
        return getattr(tp, "__origin__", None)
    def get_args(tp):
        return getattr(tp, "__args__", ())


# --- Auth Models ---

@dataclass
class TokenInfo:
    access_token: str
    token_type: str
    expires_in: int


# --- Market Data Models ---

@dataclass
class PriceResponse:
    symbol: str
    timestamp: str
    last_price: str
    currency: str


@dataclass
class OrderbookEntry:
    price: str
    volume: str


@dataclass
class OrderbookResponse:
    timestamp: str
    currency: str
    asks: List[OrderbookEntry]
    bids: List[OrderbookEntry]


@dataclass
class Trade:
    price: str
    volume: str
    timestamp: str
    currency: str


@dataclass
class PriceLimitResponse:
    timestamp: str
    currency: str
    upper_limit_price: Optional[str] = None
    lower_limit_price: Optional[str] = None


@dataclass
class Candle:
    timestamp: str
    open_price: str
    high_price: str
    low_price: str
    close_price: str
    volume: str
    currency: str


@dataclass
class CandlePageResponse:
    candles: List[Candle]
    next_before: Optional[str] = None


# --- Stock Info Models ---

@dataclass
class KrMarketDetail:
    liquidation_trading: bool
    nxt_supported: bool
    krx_trading_suspended: bool
    nxt_trading_suspended: Optional[bool] = None


@dataclass
class StockInfo:
    symbol: str
    name: str
    english_name: str
    isin_code: str
    market: str
    security_type: str
    is_common_share: bool
    status: str
    currency: str
    list_date: str
    shares_outstanding: str
    delist_date: Optional[str] = None
    leverage_factor: Optional[str] = None
    korean_market_detail: Optional[KrMarketDetail] = None


@dataclass
class StockWarning:
    warning_type: str
    exchange: str
    start_date: str
    end_date: Optional[str] = None


# --- Market Info Models ---

@dataclass
class ExchangeRateResponse:
    base_currency: str
    quote_currency: str
    rate: str
    mid_rate: str
    basis_point: str
    rate_change_type: str
    valid_from: str
    valid_until: str


@dataclass
class PreMarketSession:
    start_time: str
    end_time: str


@dataclass
class RegularMarketSession:
    start_time: str
    end_time: str


@dataclass
class AfterMarketSession:
    start_time: str
    end_time: str


@dataclass
class KrMarketDay:
    date: str
    is_business_day: bool
    is_market_opened: bool
    market_opened_description: str
    pre_market: Optional[PreMarketSession] = None
    regular_market: Optional[RegularMarketSession] = None
    after_market: Optional[AfterMarketSession] = None


@dataclass
class UsDayMarketSession:
    start_time: str
    end_time: str


@dataclass
class UsPreMarketSession:
    start_time: str
    end_time: str


@dataclass
class UsRegularMarketSession:
    start_time: str
    end_time: str


@dataclass
class UsAfterMarketSession:
    start_time: str
    end_time: str


@dataclass
class UsMarketDay:
    date: str
    is_business_day: bool
    is_market_opened: bool
    market_opened_description: str
    day_market: Optional[UsDayMarketSession] = None
    pre_market: Optional[UsPreMarketSession] = None
    regular_market: Optional[UsRegularMarketSession] = None
    after_market: Optional[UsAfterMarketSession] = None


# --- Account & Asset Models ---

@dataclass
class Account:
    account_no: str
    account_seq: int
    account_type: str


@dataclass
class Price:
    amount: str
    currency: str


@dataclass
class MarketValue:
    native: Price
    converted: Price


@dataclass
class ProfitLoss:
    native: Price
    converted: Price


@dataclass
class DailyProfitLoss:
    native: Price
    converted: Price


@dataclass
class Cost:
    native: Price
    converted: Price


@dataclass
class HoldingsItem:
    symbol: str
    name: str
    market_country: str
    currency: str
    quantity: str
    last_price: str
    average_purchase_price: str
    market_value: MarketValue
    profit_loss: ProfitLoss
    daily_profit_loss: DailyProfitLoss
    cost: Cost


@dataclass
class HoldingsOverview:
    total_purchase_amount: Price
    market_value: MarketValue
    profit_loss: ProfitLoss
    daily_profit_loss: DailyProfitLoss
    items: List[HoldingsItem]


# --- Order Models ---

@dataclass
class OrderExecutionEntry:
    execution_id: str
    price: str
    quantity: str
    executed_at: str


@dataclass
class OrderExecution:
    filled_quantity: str
    filled_amount: Optional[str] = None
    average_filled_price: Optional[str] = None
    executions: Optional[List[OrderExecutionEntry]] = None


@dataclass
class Order:
    order_id: str
    symbol: str
    side: str
    order_type: str
    time_in_force: str
    status: str
    quantity: str
    currency: str
    ordered_at: str
    execution: OrderExecution
    price: Optional[str] = None
    order_amount: Optional[str] = None
    canceled_at: Optional[str] = None


@dataclass
class OrderResponse:
    order_id: str
    client_order_id: Optional[str] = None


@dataclass
class PaginatedOrderResponse:
    orders: List[Order]
    has_next: bool
    next_cursor: Optional[str] = None


@dataclass
class BuyingPowerResponse:
    currency: str
    cash_buying_power: str


@dataclass
class SellableQuantityResponse:
    sellable_quantity: str


@dataclass
class Commission:
    market_country: str
    commission_rate: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
