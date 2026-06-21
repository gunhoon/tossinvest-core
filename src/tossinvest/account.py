from typing import List, Optional

from tossinvest.base import APIGroup
from tossinvest.models import (
    from_dict,
    Account,
    HoldingsOverview,
    BuyingPowerResponse,
    SellableQuantityResponse,
    Commission,
)


class AccountAPI(APIGroup):
    """Account and Asset API group."""

    def get_accounts(self) -> List[Account]:
        """Get list of accounts registered under this client credentials."""
        data = self._client._request("GET", "/api/v1/accounts")
        return [from_dict(Account, item) for item in data]

    def get_holdings(self, symbol: Optional[str] = None) -> HoldingsOverview:
        """Get portfolio holdings. Requires X-Tossinvest-Account header."""
        params = {}
        if symbol is not None:
            params["symbol"] = symbol
        data = self._client._request("GET", "/api/v1/holdings", params=params, account_required=True)
        return from_dict(HoldingsOverview, data)

    def get_buying_power(self, currency: str) -> BuyingPowerResponse:
        """Get current buying power for a given currency. Requires X-Tossinvest-Account header."""
        data = self._client._request(
            "GET",
            "/api/v1/buying-power",
            params={"currency": currency},
            account_required=True,
        )
        return from_dict(BuyingPowerResponse, data)

    def get_sellable_quantity(self, symbol: str) -> SellableQuantityResponse:
        """Get sellable quantity of a stock. Requires X-Tossinvest-Account header."""
        data = self._client._request(
            "GET",
            f"/api/v1/sellable-quantity",
            params={"symbol": symbol},
            account_required=True,
        )
        return from_dict(SellableQuantityResponse, data)

    def get_commissions(self) -> List[Commission]:
        """Get commissions details. Requires X-Tossinvest-Account header."""
        data = self._client._request("GET", "/api/v1/commissions", account_required=True)
        return [from_dict(Commission, item) for item in data]
