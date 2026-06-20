from typing import Any, Dict, List, Optional

from tossinvest.services.base import BaseService


class AccountService(BaseService):
    """Service to access account information and portfolio asset holdings."""

    def get_accounts(self) -> List[Dict[str, Any]]:
        """Retrieve the list of registered accounts.

        Returns:
            List of registered Account objects.
        """
        return self.client._request(
            method="GET",
            path="/api/v1/accounts",
            requires_auth=True,
            requires_account=False,
        )

    def get_holdings(
        self,
        account_seq: Optional[int] = None,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieve current stock holdings for a specific account.

        Args:
            account_seq: Account identifier. Defaults to the client-level account_seq.
            symbol: Optionally filter holdings by symbol.
        """
        params = {}
        if symbol:
            params["symbol"] = symbol

        return self.client._request(
            method="GET",
            path="/api/v1/holdings",
            params=params,
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )
