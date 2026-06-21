import time
from typing import Any, Dict, Optional

import requests

from tossinvest.exceptions import (
    TossInvestAPIError,
    TossInvestAuthError,
    TossInvestError,
    TossInvestRateLimitError,
)
from tossinvest.models import OAuth2TokenResponse
from tossinvest.services.account import AccountService
from tossinvest.services.market import MarketService
from tossinvest.services.order import OrderService


class TossInvestClient:
    """A python client for interacting with the Toss Securities Open API."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "https://openapi.tossinvest.com",
        account_seq: Optional[int] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        """Initialize the TossInvestClient and its services.

        Args:
            client_id: Toss Securities API Client ID.
            client_secret: Toss Securities API Client Secret.
            base_url: Base URL of the API. Defaults to "https://openapi.tossinvest.com".
            account_seq: Default account sequence number (X-Tossinvest-Account header).
            session: Optional pre-configured requests.Session object.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url.rstrip("/")
        self.account_seq = account_seq
        self.session = session or requests.Session()

        # Token cache state (managed inside client)
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

        # Initialize modular services
        self.market = MarketService(self)
        self.account = AccountService(self)
        self.order = OrderService(self)

    def issue_token(self) -> OAuth2TokenResponse:
        """Manually trigger OAuth2 token issuance.

        Calls the POST /oauth2/token endpoint and updates cache.

        Returns:
            OAuth2TokenResponse containing access_token, token_type, expires_in.
        """
        url = f"{self.base_url}/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = self.session.post(
                url, headers=headers, data=data, timeout=15
            )
            status_code = response.status_code
            body_text = response.text

            if status_code != 200:
                raise TossInvestAuthError(
                    f"Authentication failed with status code {status_code}: {body_text}",
                    response_body=body_text,
                )

            res_json = response.json()
            self._token = res_json["access_token"]
            expires_in = res_json["expires_in"]
            self._token_expires_at = time.time() + expires_in

            # Construct and return type-conforming dict
            return {
                "access_token": self._token,
                "token_type": "Bearer",
                "expires_in": int(max(0, self._token_expires_at - time.time())),
            }
        except TossInvestAuthError:
            raise
        except Exception as e:
            raise TossInvestAuthError(f"Failed to request OAuth2 token: {e}") from e

    def _get_valid_token(self) -> str:
        """Get a valid access token.

        Checks cache and requests a new token if expired.

        Returns:
            The active access token string.
        """
        now = time.time()
        # Add a 60-second safety buffer before token expiration
        if self._token and now < self._token_expires_at - 60:
            return self._token

        self.issue_token()
        assert self._token is not None
        return self._token

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        requires_auth: bool = True,
        requires_account: bool = False,
        account_seq: Optional[int] = None,
    ) -> Any:
        """Helper to prepare and send HTTP requests to the Toss OpenAPI."""
        url = f"{self.base_url}{path}"
        req_headers = headers.copy() if headers else {}

        if requires_auth:
            token = self._get_valid_token()
            req_headers["Authorization"] = f"Bearer {token}"

        if requires_account:
            resolved_account_seq = account_seq if account_seq is not None else self.account_seq
            if resolved_account_seq is None:
                raise TossInvestError(
                    "account_seq is required for this request. "
                    "Provide it during client initialization or pass it to the service method."
                )
            req_headers["X-Tossinvest-Account"] = str(resolved_account_seq)

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=req_headers,
                timeout=15,
            )
        except Exception as e:
            raise TossInvestError(f"HTTP request failed: {e}") from e

        # Handle HTTP error responses
        if response.status_code not in (200, 201):
            self._handle_error_response(response)

        res_json = response.json()

        # The oauth2/token endpoint does not wrap its response in standard envelope
        if path == "/oauth2/token":
            return res_json

        # All other successful API endpoints wrap payload inside "result" key
        if isinstance(res_json, dict) and "result" in res_json:
            return res_json["result"]

        return res_json

    def _handle_error_response(self, response: requests.Response) -> None:
        """Decode and raise structured TossInvest exceptions from error response."""
        status_code = response.status_code
        request_id = response.headers.get("X-Request-Id")

        try:
            err_json = response.json()
            err_details = err_json.get("error", {})
            code = err_details.get("code", "unknown-error")
            message = err_details.get("message", "An unexpected error occurred.")
            data = err_details.get("data", {})
            if not request_id:
                request_id = err_details.get("requestId")
        except Exception:
            code = "unknown-error"
            message = response.text or "An unexpected error occurred."
            data = {}

        if status_code == 429:
            # Check Retry-After header or data fields
            retry_after = response.headers.get("Retry-After")
            retry_after_sec = None
            if retry_after:
                try:
                    retry_after_sec = int(retry_after)
                except ValueError:
                    pass
            if not retry_after_sec and data:
                retry_after_sec = data.get("retryAfterSeconds")

            raise TossInvestRateLimitError(
                request_id=request_id,
                code=code,
                message=message,
                data=data,
                status_code=status_code,
                retry_after_seconds=retry_after_sec,
            )

        raise TossInvestAPIError(
            request_id=request_id,
            code=code,
            message=message,
            data=data,
            status_code=status_code,
        )
