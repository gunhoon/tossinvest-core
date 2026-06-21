from typing import List

from tossinvest.base import APIGroup
from tossinvest.exceptions import TossInvestError
from tossinvest.models import from_dict, StockInfo, StockWarning


class StockInfoAPI(APIGroup):
    """Stock Info API group (static reference data for stocks)."""

    def get_stocks(self, symbols: List[str]) -> List[StockInfo]:
        """Get basic reference info for a list of symbols (up to 200)."""
        if not symbols:
            raise TossInvestError("symbols list cannot be empty")
        symbols_str = ",".join(symbols)
        data = self._client._request("GET", "/api/v1/stocks", params={"symbols": symbols_str})
        return [from_dict(StockInfo, item) for item in data]

    def get_warnings(self, symbol: str) -> List[StockWarning]:
        """Get trading warning flags or volatility interruption (VI) events for a symbol."""
        data = self._client._request("GET", f"/api/v1/stocks/{symbol}/warnings")
        return [from_dict(StockWarning, item) for item in data]
