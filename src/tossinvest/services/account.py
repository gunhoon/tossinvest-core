from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import TossInvestClient

class AccountService:
    """Handles account listing and asset holdings retrieval."""
    
    def __init__(self, client: "TossInvestClient"):
        self.client = client
        
    def get_accounts(self) -> Dict[str, Any]:
        """계좌 목록 조회.
        
        GET /api/v1/accounts
        """
        # Account listing itself does not require X-Tossinvest-Account header
        return self.client.request(
            method="GET",
            path="/api/v1/accounts",
            use_auth=True,
            require_account=False
        )
        
    def get_holdings(
        self,
        symbol: Optional[str] = None,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """보유 주식 조회.
        
        GET /api/v1/holdings
        """
        params = {}
        if symbol is not None:
            params["symbol"] = symbol
            
        return self.client.request(
            method="GET",
            path="/api/v1/holdings",
            use_auth=True,
            require_account=True,
            account_seq=account_seq,
            params=params
        )
