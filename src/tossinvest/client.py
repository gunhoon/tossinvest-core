import logging
import time
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import requests

from .exceptions import raise_for_status, TossInvestError
from .services import AuthService, MarketService, AccountService, OrderService

logger = logging.getLogger("tossinvest")

class TossInvestClient:
    """Central client for Toss Securities Open API.
    
    Manages authentication token lifecycle, automatic retries on 401 (expired token),
    and rate limit handling (429) using Retry-After.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "https://openapi.tossinvest.com",
        account_seq: Optional[int] = None,
        auto_retry_rate_limit: bool = True,
        max_rate_limit_retries: int = 3,
    ):
        """Initializes the TossInvestClient.
        
        Args:
            client_id: Your Toss Open API client ID.
            client_secret: Your Toss Open API client secret.
            base_url: Base API server URL. Defaults to 'https://openapi.tossinvest.com'.
            account_seq: Default account sequence (accountSeq) to use for account-related APIs.
            auto_retry_rate_limit: If True, sleep and retry when receiving HTTP 429 Rate Limit.
            max_rate_limit_retries: Maximum number of retries for rate limited requests.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.account_seq = account_seq
        self.auto_retry_rate_limit = auto_retry_rate_limit
        self.max_rate_limit_retries = max_rate_limit_retries
        
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "tossinvest-python-sdk/1.0.0",
        })
        
        # Token cache
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0
        
        # Rate limit info from the last API call
        self.rate_limit_info: Dict[str, Any] = {}
        
        # Initialize services
        self.auth = AuthService(self)
        self.market = MarketService(self)
        self.account = AccountService(self)
        self.order = OrderService(self)
        
    def _update_rate_limit_info(self, headers: requests.structures.CaseInsensitiveDict) -> None:
        """Parses rate limit information from response headers."""
        if "X-RateLimit-Limit" in headers:
            try:
                self.rate_limit_info["limit"] = int(headers["X-RateLimit-Limit"])
            except ValueError:
                pass
        if "X-RateLimit-Remaining" in headers:
            try:
                self.rate_limit_info["remaining"] = int(headers["X-RateLimit-Remaining"])
            except ValueError:
                pass
        if "X-RateLimit-Reset" in headers:
            try:
                self.rate_limit_info["reset"] = float(headers["X-RateLimit-Reset"])
            except ValueError:
                self.rate_limit_info["reset"] = headers["X-RateLimit-Reset"]

    def request(
        self,
        method: str,
        path: str,
        use_auth: bool = True,
        require_account: bool = False,
        account_seq: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Sends an HTTP request to the Toss API, handling auth, rate-limiting, and errors."""
        url = urljoin(self.base_url, path)
        
        # Build headers
        req_headers = headers or {}
        
        if use_auth:
            token = self.auth.get_token()
            req_headers["Authorization"] = f"Bearer {token}"
            
        if require_account:
            # Determine account sequence: method arg overrides client default
            seq = account_seq if account_seq is not None else self.account_seq
            if seq is None:
                raise TossInvestError(
                    "account_seq is required for this request. "
                    "Please set self.account_seq or pass the account_seq parameter to the method."
                )
            req_headers["X-Tossinvest-Account"] = str(seq)
            
        # Helper to execute the actual call
        def execute_call() -> requests.Response:
            merged_headers = {**req_headers}
            if "headers" in kwargs:
                # Merge explicitly passed headers in kwargs
                extra_headers = kwargs.pop("headers") or {}
                merged_headers.update(extra_headers)
            return self.session.request(method, url, headers=merged_headers, params=params, **kwargs)

        rate_limit_retry_count = 0
        while True:
            response = execute_call()
            self._update_rate_limit_info(response.headers)
            
            # 1. Handle Rate Limiting (429)
            if response.status_code == 429:
                if self.auto_retry_rate_limit and rate_limit_retry_count < self.max_rate_limit_retries:
                    rate_limit_retry_count += 1
                    # Check Retry-After header, default to 1.0s
                    retry_after_str = response.headers.get("Retry-After")
                    try:
                        retry_after = float(retry_after_str) if retry_after_str else 1.0
                    except ValueError:
                        retry_after = 1.0
                        
                    logger.warning(
                        f"Rate limit exceeded (429). Retrying in {retry_after}s... "
                        f"(Attempt {rate_limit_retry_count}/{self.max_rate_limit_retries})"
                    )
                    time.sleep(retry_after)
                    continue
                else:
                    # Raise the rate limit exception
                    try:
                        res_json = response.json()
                    except Exception:
                        res_json = None
                    raise_for_status(response.status_code, res_json, response.headers)
                    
            # 2. Handle Token Expiration (401)
            if response.status_code == 401:
                try:
                    res_json = response.json()
                except Exception:
                    res_json = None
                
                error_code = ""
                if res_json and isinstance(res_json, dict) and "error" in res_json:
                    error_code = res_json["error"].get("code", "")
                
                # If token is expired or invalid, and we are using auth, force refresh token and retry once
                if use_auth and error_code in ("expired-token", "invalid-token"):
                    logger.info("Access token expired/invalid. Refreshing and retrying...")
                    # Force issue a new token
                    self.auth.issue_token()
                    # Update header and retry
                    req_headers["Authorization"] = f"Bearer {self._access_token}"
                    use_auth = False # Prevent infinite retry loop for auth issues
                    continue
                    
            # 3. Process normal responses or throw other exceptions
            try:
                res_json = response.json()
            except Exception:
                res_json = None
                
            raise_for_status(response.status_code, res_json, response.headers)
            return res_json or {}
