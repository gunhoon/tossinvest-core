import time
from typing import Any, Dict, Optional

import requests

from tossinvest.exceptions import (
    TossInvestAPIError,
    TossInvestAuthError,
    TossInvestError,
    TossInvestRateLimitError,
)
from tossinvest.services.account import AccountService
from tossinvest.services.market import MarketService
from tossinvest.services.order import OrderService


class TossInvestClient:
    """A python client for interacting with the Toss Securities Open API."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        account_seq: Optional[int] = None,
        max_retries: int = 3,
    ) -> None:
        """Initialize the TossInvestClient and its services.

        Args:
            client_id: Toss Securities API Client ID.
            client_secret: Toss Securities API Client Secret.
            account_seq: Default account sequence number (X-Tossinvest-Account header).
            max_retries: Maximum number of retries for 429 rate limit errors. Defaults to 3.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.account_seq = account_seq
        self.max_retries = max_retries

        self.base_url = "https://openapi.tossinvest.com"
        self.session = requests.Session()

        # Token cache state (managed inside client)
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

        # Initialize modular services
        self.market = MarketService(self)
        self.account = AccountService(self)
        self.order = OrderService(self)

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
            self._token_expires_at = time.time() + res_json["expires_in"]
            return self._token
        except TossInvestAuthError:
            raise
        except Exception as e:
            raise TossInvestAuthError(f"Failed to request OAuth2 token: {e}") from e

    def _get_retry_after(self, response: requests.Response) -> Optional[int]:
        """Extract retry-after seconds from response headers or body."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                pass
        try:
            err_json = response.json()
            err_details = err_json.get("error", {})
            data = err_details.get("data", {})
            if isinstance(data, dict):
                val = data.get("retryAfterSeconds")
                if val is not None:
                    return int(val)
        except Exception:
            pass
        return None

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

        if requires_account:
            resolved_account_seq = account_seq if account_seq is not None else self.account_seq
            if resolved_account_seq is None:
                raise TossInvestError(
                    "account_seq is required for this request. "
                    "Provide it during client initialization or pass it to the service method."
                )
            req_headers["X-Tossinvest-Account"] = str(resolved_account_seq)

        response = None
        for attempt in range(self.max_retries + 1):
            if requires_auth:
                token = self._get_valid_token()
                req_headers["Authorization"] = f"Bearer {token}"

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

            # Handle 429 Rate Limit with Retry-After header/body
            if response.status_code == 429 and attempt < self.max_retries:
                retry_after_sec = self._get_retry_after(response) or 1
                time.sleep(retry_after_sec)
                continue

            # Handle other HTTP error responses
            if response.status_code not in (200, 201):
                self._handle_error_response(response)

            break

        if response is None:
            raise TossInvestError("Request completed with no response.")

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
