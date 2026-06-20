import time
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import TossInvestClient

class AuthService:
    """Handles OAuth 2.0 token issuance and management."""
    
    def __init__(self, client: "TossInvestClient"):
        self.client = client
        
    def issue_token(self) -> Dict[str, Any]:
        """Issues an OAuth 2.0 access token (Client Credentials Grant).
        
        Calls POST /oauth2/token. Caches the token on the client.
        """
        path = "/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client.client_id,
            "client_secret": self.client.client_secret,
        }
        
        # We pass use_auth=False because token issuance itself doesn't use bearer token auth.
        response = self.client.request(
            method="POST",
            path=path,
            use_auth=False,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = response.get("access_token")
        expires_in = response.get("expires_in", 86400)
        
        self.client._access_token = token
        # Cache expires_at with 30s buffer to prevent edge-case timing issues
        self.client._token_expires_at = time.time() + float(expires_in) - 30.0
        
        return response
        
    def get_token(self) -> str:
        """Returns the cached token, or fetches a new one if not present or expired."""
        if not self.client._access_token or time.time() >= self.client._token_expires_at:
            self.issue_token()
        
        assert self.client._access_token is not None
        return self.client._access_token
