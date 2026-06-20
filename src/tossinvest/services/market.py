from typing import Any, Dict, List, Optional

from tossinvest.services.base import BaseService


class MarketService(BaseService):
    """Service to access market data, stock master info, exchange rates, and calendars."""

    def get_prices(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Retrieve current prices of stock symbols (up to 200 symbols).

        Args:
            symbols: List of symbols (e.g. ['005930', 'AAPL']).
        """
        if not symbols:
            raise ValueError("symbols list cannot be empty.")
        symbols_str = ",".join(symbols)
        return self.client._request(
            method="GET",
            path="/api/v1/prices",
            params={"symbols": symbols_str},
        )

    def get_orderbook(self, symbol: str) -> Dict[str, Any]:
        """Retrieve orderbook (bids/asks) and volume for a symbol.

        Args:
            symbol: Stock symbol (e.g. '005930' or 'AAPL').
        """
        return self.client._request(
            method="GET",
            path="/api/v1/orderbook",
            params={"symbol": symbol},
        )

    def get_candles(
        self,
        symbol: str,
        interval: str,
        count: Optional[int] = None,
        before: Optional[str] = None,
        adjusted: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Retrieve candle chart data (OHLCV) for a symbol.

        Args:
            symbol: Stock symbol.
            interval: Bar unit ('1m' or '1d').
            count: Number of candles to retrieve (max 200).
            before: Pagination upper limit (exclusive, ISO 8601 string).
            adjusted: Whether to apply adjusted price (default: True).
        """
        params = {"symbol": symbol, "interval": interval}
        if count is not None:
            params["count"] = count
        if before is not None:
            params["before"] = before
        if adjusted is not None:
            params["adjusted"] = "true" if adjusted else "false"

        return self.client._request(
            method="GET",
            path="/api/v1/candles",
            params=params,
        )

    def get_price_limits(self, symbol: str) -> Dict[str, Any]:
        """Retrieve upper/lower price limits for a symbol.

        Args:
            symbol: Stock symbol.
        """
        return self.client._request(
            method="GET",
            path="/api/v1/price-limits",
            params={"symbol": symbol},
        )

    def get_trades(self, symbol: str, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve recent trade/execution history for a symbol.

        Args:
            symbol: Stock symbol.
            count: Number of trades to retrieve (max 50).
        """
        params = {"symbol": symbol}
        if count is not None:
            params["count"] = count
        return self.client._request(
            method="GET",
            path="/api/v1/trades",
            params=params,
        )

    def get_stocks(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Retrieve master data for stock symbols (up to 200 symbols).

        Args:
            symbols: List of symbols (e.g. ['005930', 'AAPL']).
        """
        if not symbols:
            raise ValueError("symbols list cannot be empty.")
        symbols_str = ",".join(symbols)
        return self.client._request(
            method="GET",
            path="/api/v1/stocks",
            params={"symbols": symbols_str},
        )

    def get_stock_warnings(self, symbol: str) -> List[Dict[str, Any]]:
        """Retrieve market warnings / warnings for a stock.

        Args:
            symbol: Stock symbol.
        """
        return self.client._request(
            method="GET",
            path=f"/api/v1/stocks/{symbol}/warnings",
        )

    def get_exchange_rate(
        self,
        base_currency: str = "USD",
        quote_currency: str = "KRW",
        date_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieve KRW/USD exchange rate.

        Args:
            base_currency: Base currency (e.g. 'USD').
            quote_currency: Quote currency (e.g. 'KRW').
            date_time: ISO 8601 timestamp for historical exchange rate.
        """
        params = {
            "baseCurrency": base_currency,
            "quoteCurrency": quote_currency,
        }
        if date_time:
            params["dateTime"] = date_time
        return self.client._request(
            method="GET",
            path="/api/v1/exchange-rate",
            params=params,
        )

    def get_market_calendar(self, country: str, date: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve market calendar / operating hours for KR or US.

        Args:
            country: Country code ('KR' or 'US').
            date: Base date (YYYY-MM-DD).
        """
        country_upper = country.upper()
        if country_upper not in ("KR", "US"):
            raise ValueError("country must be 'KR' or 'US'.")

        params = {}
        if date:
            params["date"] = date

        return self.client._request(
            method="GET",
            path=f"/api/v1/market-calendar/{country_upper}",
            params=params,
        )
