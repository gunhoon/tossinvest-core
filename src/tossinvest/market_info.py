from typing import Optional

from tossinvest.base import APIGroup
from tossinvest.models import from_dict, ExchangeRateResponse, KrMarketDay, UsMarketDay


class MarketInfoAPI(APIGroup):
    """Market Info API group (exchange rates and calendar operations)."""

    def get_exchange_rate(
        self,
        base_currency: str,
        quote_currency: str,
        date_time: Optional[str] = None,
    ) -> ExchangeRateResponse:
        """Get KRW/USD exchange rates."""
        params = {"baseCurrency": base_currency, "quoteCurrency": quote_currency}
        if date_time is not None:
            params["dateTime"] = date_time
        data = self._client._request("GET", "/api/v1/exchange-rate", params=params)
        return from_dict(ExchangeRateResponse, data)

    def get_kr_calendar(self, date: Optional[str] = None) -> KrMarketDay:
        """Get Korean market calendar operations detail for a date (YYYY-MM-DD)."""
        params = {}
        if date is not None:
            params["date"] = date
        data = self._client._request("GET", "/api/v1/market-calendar/KR", params=params)
        return from_dict(KrMarketDay, data)

    def get_us_calendar(self, date: Optional[str] = None) -> UsMarketDay:
        """Get US market calendar operations detail for a date (YYYY-MM-DD)."""
        params = {}
        if date is not None:
            params["date"] = date
        data = self._client._request("GET", "/api/v1/market-calendar/US", params=params)
        return from_dict(UsMarketDay, data)
