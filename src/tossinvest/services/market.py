from typing import Dict, Any, List, Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import TossInvestClient

class MarketService:
    """Handles market data, stock master info, exchange rates, and market calendars."""
    
    def __init__(self, client: "TossInvestClient"):
        self.client = client
        
    def _format_symbols(self, symbols: Union[str, List[str]]) -> str:
        """Helper to convert symbols list or string to comma-separated string."""
        if isinstance(symbols, list):
            return ",".join(symbols)
        return symbols

    def get_orderbook(self, symbol: str) -> Dict[str, Any]:
        """호가 조회.
        
        GET /api/v1/orderbook
        """
        return self.client.request(
            method="GET",
            path="/api/v1/orderbook",
            params={"symbol": symbol}
        )

    def get_prices(self, symbols: Union[str, List[str]]) -> Dict[str, Any]:
        """현재가 조회.
        
        GET /api/v1/prices
        """
        return self.client.request(
            method="GET",
            path="/api/v1/prices",
            params={"symbols": self._format_symbols(symbols)}
        )

    def get_trades(self, symbol: str, count: Optional[int] = None) -> Dict[str, Any]:
        """최근 체결 내역 조회.
        
        GET /api/v1/trades
        """
        params = {"symbol": symbol}
        if count is not None:
            params["count"] = count
        return self.client.request(
            method="GET",
            path="/api/v1/trades",
            params=params
        )

    def get_price_limits(self, symbol: str) -> Dict[str, Any]:
        """상/하한가 조회.
        
        GET /api/v1/price-limits
        """
        return self.client.request(
            method="GET",
            path="/api/v1/price-limits",
            params={"symbol": symbol}
        )

    def get_candles(
        self,
        symbol: str,
        interval: str,
        count: Optional[int] = None,
        before: Optional[str] = None,
        adjusted: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """캔들 차트 조회 (1분봉, 일봉).
        
        GET /api/v1/candles
        """
        params = {
            "symbol": symbol,
            "interval": interval,
        }
        if count is not None:
            params["count"] = count
        if before is not None:
            params["before"] = before
        if adjusted is not None:
            params["adjusted"] = adjusted
            
        return self.client.request(
            method="GET",
            path="/api/v1/candles",
            params=params
        )

    def get_stocks(self, symbols: Union[str, List[str]]) -> Dict[str, Any]:
        """종목 기본 정보 조회.
        
        GET /api/v1/stocks
        """
        return self.client.request(
            method="GET",
            path="/api/v1/stocks",
            params={"symbols": self._format_symbols(symbols)}
        )

    def get_stock_warnings(self, symbol: str) -> Dict[str, Any]:
        """매수 유의사항 조회.
        
        GET /api/v1/stocks/{symbol}/warnings
        """
        return self.client.request(
            method="GET",
            path=f"/api/v1/stocks/{symbol}/warnings"
        )

    def get_exchange_rate(
        self,
        base_currency: str,
        quote_currency: str,
        date_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """KRW↔USD 환율 조회.
        
        GET /api/v1/exchange-rate
        """
        params = {
            "baseCurrency": base_currency,
            "quoteCurrency": quote_currency,
        }
        if date_time is not None:
            params["dateTime"] = date_time
            
        return self.client.request(
            method="GET",
            path="/api/v1/exchange-rate",
            params=params
        )

    def get_kr_market_calendar(self, date: Optional[str] = None) -> Dict[str, Any]:
        """국내 장 운영 정보 조회.
        
        GET /api/v1/market-calendar/KR
        """
        params = {}
        if date is not None:
            params["date"] = date
        return self.client.request(
            method="GET",
            path="/api/v1/market-calendar/KR",
            params=params
        )

    def get_us_market_calendar(self, date: Optional[str] = None) -> Dict[str, Any]:
        """해외 장 운영 정보 조회.
        
        GET /api/v1/market-calendar/US
        """
        params = {}
        if date is not None:
            params["date"] = date
        return self.client.request(
            method="GET",
            path="/api/v1/market-calendar/US",
            params=params
        )
