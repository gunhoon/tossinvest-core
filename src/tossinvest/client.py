import time
from typing import Any, Dict, List, Optional, Union

import requests

from tossinvest.exceptions import (
    TossInvestAPIError,
    TossInvestAuthError,
    TossInvestError,
    TossInvestRateLimitError,
)


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
        """Initialize the TossInvestClient.

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

        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def _get_valid_token(self) -> str:
        """Retrieve a cached access token or request a new one if expired."""
        now = time.time()
        # Add a 60-second safety buffer before token expiration
        if self._token and now < self._token_expires_at - 60:
            return self._token

        self._refresh_token()
        assert self._token is not None
        return self._token

    def _refresh_token(self) -> None:
        """Call the OAuth2 token endpoint to obtain a new access token."""
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
            response = self.session.post(url, headers=headers, data=data, timeout=15)
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
        except TossInvestAuthError:
            raise
        except Exception as e:
            raise TossInvestAuthError(f"Failed to request OAuth2 token: {e}") from e

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
                    "Provide it during client initialization or pass it to the method call."
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

    # ==========================================
    # 1. AUTHENTICATION (인증)
    # ==========================================

    def issue_token(self) -> Dict[str, Any]:
        """Manually trigger OAuth2 token issuance.

        Returns:
            Dict containing access_token, token_type, expires_in.
        """
        # This will internally invoke _refresh_token and cache the results
        self._refresh_token()
        return {
            "access_token": self._token,
            "token_type": "Bearer",
            "expires_in": int(max(0, self._token_expires_at - time.time())),
        }

    # ==========================================
    # 2. MARKET DATA (시세 조회)
    # ==========================================

    def get_prices(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Retrieve current prices of stock symbols (up to 200 symbols).

        Args:
            symbols: List of symbols (e.g. ['005930', 'AAPL']).
        """
        if not symbols:
            raise ValueError("symbols list cannot be empty.")
        symbols_str = ",".join(symbols)
        return self._request(
            method="GET",
            path="/api/v1/prices",
            params={"symbols": symbols_str},
        )

    def get_orderbook(self, symbol: str) -> Dict[str, Any]:
        """Retrieve orderbook (bids/asks) and volume for a symbol.

        Args:
            symbol: Stock symbol (e.g. '005930' or 'AAPL').
        """
        return self._request(
            method="GET",
            path="/api/v1/orderbook",
            params={"symbol": symbol},
        )

    def get_candles(
        self,
        symbol: str,
        interval: str,
        count: Optional[int] = None,
        before: Optional[str] = None,
        adjusted: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Retrieve candle chart data (OHLCV) for a symbol.

        Args:
            symbol: Stock symbol.
            interval: Bar unit ('1m' or '1d').
            count: Number of candles to retrieve (max 200).
            before: Pagination upper limit (exclusive, ISO 8601 string).
            adjusted: Whether to apply adjusted price (default: True).
        """
        params = {"symbol": symbol, "interval": interval}
        if count is not None:
            params["count"] = count
        if before is not None:
            params["before"] = before
        if adjusted is not None:
            params["adjusted"] = "true" if adjusted else "false"

        return self._request(
            method="GET",
            path="/api/v1/candles",
            params=params,
        )

    def get_price_limits(self, symbol: str) -> Dict[str, Any]:
        """Retrieve upper/lower price limits for a symbol.

        Args:
            symbol: Stock symbol.
        """
        return self._request(
            method="GET",
            path="/api/v1/price-limits",
            params={"symbol": symbol},
        )

    def get_trades(self, symbol: str, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve recent trade/execution history for a symbol.

        Args:
            symbol: Stock symbol.
            count: Number of trades to retrieve (max 50).
        """
        params = {"symbol": symbol}
        if count is not None:
            params["count"] = count
        return self._request(
            method="GET",
            path="/api/v1/trades",
            params=params,
        )

    # ==========================================
    # 3. STOCK & MARKET INFO (종목/시장 정보 조회)
    # ==========================================

    def get_stocks(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Retrieve master data for stock symbols (up to 200 symbols).

        Args:
            symbols: List of symbols (e.g. ['005930', 'AAPL']).
        """
        if not symbols:
            raise ValueError("symbols list cannot be empty.")
        symbols_str = ",".join(symbols)
        return self._request(
            method="GET",
            path="/api/v1/stocks",
            params={"symbols": symbols_str},
        )

    def get_stock_warnings(self, symbol: str) -> List[Dict[str, Any]]:
        """Retrieve market warnings / warnings for a stock.

        Args:
            symbol: Stock symbol.
        """
        return self._request(
            method="GET",
            path=f"/api/v1/stocks/{symbol}/warnings",
        )

    def get_exchange_rate(
        self,
        base_currency: str = "USD",
        quote_currency: str = "KRW",
        date_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieve KRW/USD exchange rate.

        Args:
            base_currency: Base currency (e.g. 'USD').
            quote_currency: Quote currency (e.g. 'KRW').
            date_time: ISO 8601 timestamp for historical exchange rate.
        """
        params = {
            "baseCurrency": base_currency,
            "quoteCurrency": quote_currency,
        }
        if date_time:
            params["dateTime"] = date_time
        return self._request(
            method="GET",
            path="/api/v1/exchange-rate",
            params=params,
        )

    def get_market_calendar(self, country: str, date: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve market calendar / operating hours for KR or US.

        Args:
            country: Country code ('KR' or 'US').
            date: Base date (YYYY-MM-DD).
        """
        country_upper = country.upper()
        if country_upper not in ("KR", "US"):
            raise ValueError("country must be 'KR' or 'US'.")

        params = {}
        if date:
            params["date"] = date

        return self._request(
            method="GET",
            path=f"/api/v1/market-calendar/{country_upper}",
            params=params,
        )

    # ==========================================
    # 4. ACCOUNT & ASSET (계좌/자산 조회)
    # ==========================================

    def get_accounts(self) -> List[Dict[str, Any]]:
        """Retrieve the list of registered accounts.

        Returns:
            List of registered Account objects.
        """
        return self._request(
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

        return self._request(
            method="GET",
            path="/api/v1/holdings",
            params=params,
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )

    # ==========================================
    # 5. ORDERING (주식 주문)
    # ==========================================

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Optional[str] = None,
        price: Optional[str] = None,
        order_amount: Optional[str] = None,
        time_in_force: str = "DAY",
        client_order_id: Optional[str] = None,
        confirm_high_value_order: bool = False,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a new stock order (Buy/Sell, Limit/Market, KR/US).

        Args:
            symbol: Stock symbol.
            side: 'BUY' or 'SELL'.
            order_type: 'LIMIT' or 'MARKET'.
            quantity: Order quantity in shares. (required for quantity-based orders).
            price: Order price. (required for LIMIT orders).
            order_amount: Order amount in USD. (US Market amount-based orders only).
            time_in_force: 'DAY' (default) or 'CLS'.
            client_order_id: Client-side unique identifier for idempotency.
            confirm_high_value_order: Confirm flag for orders >= 100M KRW.
            account_seq: Account identifier. Defaults to the client-level account_seq.
        """
        body = {
            "symbol": symbol,
            "side": side.upper(),
            "orderType": order_type.upper(),
            "timeInForce": time_in_force.upper(),
            "confirmHighValueOrder": confirm_high_value_order,
        }

        if quantity is not None:
            body["quantity"] = str(quantity)
        if price is not None:
            body["price"] = str(price)
        if order_amount is not None:
            body["orderAmount"] = str(order_amount)
        if client_order_id is not None:
            body["clientOrderId"] = client_order_id

        return self._request(
            method="POST",
            path="/api/v1/orders",
            json=body,
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )

    def modify_order(
        self,
        order_id: str,
        order_type: str,
        quantity: Optional[str] = None,
        price: Optional[str] = None,
        confirm_high_value_order: bool = False,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Modify an existing pending order (price and/or quantity).

        Args:
            order_id: Order identifier to modify.
            order_type: 'LIMIT' or 'MARKET'.
            quantity: New quantity (KR stock only).
            price: New price (required for LIMIT orders).
            confirm_high_value_order: Confirm flag for orders >= 100M KRW.
            account_seq: Account identifier. Defaults to the client-level account_seq.
        """
        body = {
            "orderType": order_type.upper(),
            "confirmHighValueOrder": confirm_high_value_order,
        }

        if quantity is not None:
            body["quantity"] = str(quantity)
        if price is not None:
            body["price"] = str(price)

        return self._request(
            method="POST",
            path=f"/api/v1/orders/{order_id}/modify",
            json=body,
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )

    def cancel_order(
        self,
        order_id: str,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Cancel an existing pending order.

        Args:
            order_id: Order identifier to cancel.
            account_seq: Account identifier. Defaults to the client-level account_seq.
        """
        return self._request(
            method="POST",
            path=f"/api/v1/orders/{order_id}/cancel",
            json={},
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )

    def get_orders(
        self,
        status: str,
        symbol: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Retrieve order history.

        Args:
            status: Filter by status group ('OPEN' or 'CLOSED').
            symbol: Filter by symbol.
            from_date: Query start date (YYYY-MM-DD).
            to_date: Query end date (YYYY-MM-DD).
            cursor: Pagination cursor (CLOSED orders only).
            limit: Number of records per page (CLOSED orders only).
            account_seq: Account identifier. Defaults to the client-level account_seq.
        """
        params = {"status": status.upper()}

        if symbol:
            params["symbol"] = symbol
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if cursor:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit

        return self._request(
            method="GET",
            path="/api/v1/orders",
            params=params,
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )

    def get_order(
        self,
        order_id: str,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Retrieve detailed information for a specific order.

        Args:
            order_id: Order identifier.
            account_seq: Account identifier. Defaults to the client-level account_seq.
        """
        return self._request(
            method="GET",
            path=f"/api/v1/orders/{order_id}",
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )

    def get_buying_power(
        self,
        currency: str = "KRW",
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Retrieve buying power (cash available to buy).

        Args:
            currency: Currency code (e.g. 'KRW' or 'USD').
            account_seq: Account identifier. Defaults to the client-level account_seq.
        """
        return self._request(
            method="GET",
            path="/api/v1/buying-power",
            params={"currency": currency.upper()},
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )

    def get_sellable_quantity(
        self,
        symbol: str,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Retrieve sellable quantity of a symbol.

        Args:
            symbol: Stock symbol.
            account_seq: Account identifier. Defaults to the client-level account_seq.
        """
        return self._request(
            method="GET",
            path="/api/v1/sellable-quantity",
            params={"symbol": symbol},
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )

    def get_commissions(
        self,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Retrieve trading commission rates for KR/US markets.

        Args:
            account_seq: Account identifier. Defaults to the client-level account_seq.
        """
        return self._request(
            method="GET",
            path="/api/v1/commissions",
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )
