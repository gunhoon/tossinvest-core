import time
from typing import Any, Dict, Optional
import requests

from tossinvest.exceptions import (
    TossInvestError,
    TossInvestAuthError,
    TossInvestAPIError,
)
from tossinvest.models import from_dict, TokenInfo
from tossinvest.market import MarketDataAPI
from tossinvest.stock import StockInfoAPI
from tossinvest.market_info import MarketInfoAPI
from tossinvest.account import AccountAPI
from tossinvest.order import OrderAPI


class TossInvestClient:
    """Core Toss Securities Open API Python Client."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "https://openapi.tossinvest.com",
        timeout: float = 10.0,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._account_seq: Optional[int] = None

        # API Namespaces
        self.market = MarketDataAPI(self)
        self.stock = StockInfoAPI(self)
        self.market_info = MarketInfoAPI(self)
        self.account = AccountAPI(self)
        self.order = OrderAPI(self)

    @property
    def account_seq(self) -> Optional[int]:
        """Get the default X-Tossinvest-Account sequence identifier."""
        return self._account_seq

    @account_seq.setter
    def account_seq(self, val: Optional[int]):
        """Set the default X-Tossinvest-Account sequence identifier."""
        self._account_seq = val

    def set_account_seq(self, account_seq: int) -> None:
        """Set the default X-Tossinvest-Account sequence identifier (helper method)."""
        self._account_seq = account_seq

    def _ensure_token(self) -> str:
        """Ensures that a valid access token is cached, requesting a new one if expired."""
        if not self._token or (self._token_expires_at - time.time() < 60):
            self.issue_token()
        return self._token

    def issue_token(self) -> TokenInfo:
        """Manually issues/refreshes the OAuth2 token."""
        url = f"{self.base_url}/oauth2/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        # Call low-level post without _ensure_token
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=self.timeout)
            data = self._handle_response(response, is_oauth=True)
            
            token_info = from_dict(TokenInfo, data)
            self._token = token_info.access_token
            self._token_expires_at = time.time() + token_info.expires_in
            return token_info
        except requests.RequestException as e:
            raise TossInvestAuthError("connection_error", str(e), status_code=500)

    def _request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        account_required: bool = False,
        account_seq_override: Optional[int] = None,
    ) -> Any:
        """Unified internal request execution with token injection and error handling."""
        token = self._ensure_token()
        
        req_headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        if headers:
            req_headers.update(headers)

        if account_required:
            seq = account_seq_override if account_seq_override is not None else self._account_seq
            if seq is None:
                raise TossInvestError(
                    "This endpoint requires an account sequence (X-Tossinvest-Account header). "
                    "Please set client.account_seq = <seq> or call the endpoint with an override."
                )
            req_headers["X-Tossinvest-Account"] = str(seq)

        url = f"{self.base_url}{path}"
        try:
            response = requests.request(
                method,
                url,
                headers=req_headers,
                params=params,
                json=json,
                data=data,
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            if isinstance(e, (TossInvestError, TossInvestAPIError, TossInvestAuthError)):
                raise e
            raise TossInvestError(f"HTTP request failed: {e}")

    def _handle_response(self, response: requests.Response, is_oauth: bool = False) -> Any:
        """Decodes JSON response, wrapping any errors into structured custom exceptions."""
        if not (200 <= response.status_code < 300):
            try:
                err_json = response.json()
                if isinstance(err_json, dict):
                    if "error" in err_json:
                        err = err_json["error"]
                        if isinstance(err, dict):
                            # Toss invest API specific error
                            raise TossInvestAPIError(
                                status_code=response.status_code,
                                request_id=err.get("requestId", ""),
                                code=err.get("code", "unknown"),
                                message=err.get("message", ""),
                                data=err.get("data"),
                            )
                        else:
                            # OAuth2 spec standard error where 'error' is a string
                            raise TossInvestAuthError(
                                error=str(err),
                                error_description=err_json.get("error_description", ""),
                                status_code=response.status_code,
                            )
            except (ValueError, KeyError, AttributeError) as e:
                # Fallback to standard HTTP exception if not parseable
                if isinstance(e, (TossInvestAPIError, TossInvestAuthError)):
                    raise e

            # General request failure fallback
            raise TossInvestError(f"API request failed with code {response.status_code}: {response.text}")

        try:
            res_json = response.json()
            if is_oauth:
                return res_json
            
            # Toss BFF endpoints wrap success payloads in {"result": ...}
            if isinstance(res_json, dict) and "result" in res_json:
                return res_json["result"]
            
            return res_json
        except ValueError as e:
            raise TossInvestError(f"Response is not a valid JSON: {e}")
