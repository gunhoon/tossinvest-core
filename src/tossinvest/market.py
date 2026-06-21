from typing import List, Optional

from tossinvest.base import APIGroup
from tossinvest.exceptions import TossInvestError
from tossinvest.models import (
    from_dict,
    PriceResponse,
    OrderbookResponse,
    Trade,
    PriceLimitResponse,
    CandlePageResponse,
)


class MarketDataAPI(APIGroup):
    """Market Data API group (endpoints that retrieve real-time and historical price data)."""

    def get_orderbook(self, symbol: str) -> OrderbookResponse:
        """Get order book (bid/ask bids and volume) for a given symbol."""
        data = self._client._request("GET", "/api/v1/orderbook", params={"symbol": symbol})
        return from_dict(OrderbookResponse, data)

    def get_prices(self, symbols: List[str]) -> List[PriceResponse]:
        """Get current prices for a list of symbols (up to 200)."""
        if not symbols:
            raise TossInvestError("symbols list cannot be empty")
        symbols_str = ",".join(symbols)
        data = self._client._request("GET", "/api/v1/prices", params={"symbols": symbols_str})
        return [from_dict(PriceResponse, item) for item in data]

    def get_trades(self, symbol: str, count: Optional[int] = None) -> List[Trade]:
        """Get recent trades for a given symbol (count up to 50)."""
        params = {"symbol": symbol}
        if count is not None:
            params["count"] = count
        data = self._client._request("GET", "/api/v1/trades", params=params)
        return [from_dict(Trade, item) for item in data]

    def get_price_limits(self, symbol: str) -> PriceLimitResponse:
        """Get today's upper and lower price limits for a symbol."""
        data = self._client._request("GET", "/api/v1/price-limits", params={"symbol": symbol})
        return from_dict(PriceLimitResponse, data)

    def get_candles(
        self,
        symbol: str,
        interval: str,
        count: Optional[int] = None,
        before: Optional[str] = None,
        adjusted: Optional[bool] = None,
    ) -> CandlePageResponse:
        """Get candle charts (OHLCV) for a symbol."""
        params = {"symbol": symbol, "interval": interval}
        if count is not None:
            params["count"] = count
        if before is not None:
            params["before"] = before
        if adjusted is not None:
            params["adjusted"] = "true" if adjusted else "false"

        data = self._client._request("GET", "/api/v1/candles", params=params)
        return from_dict(CandlePageResponse, data)
