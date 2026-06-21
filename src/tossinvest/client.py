import time
from typing import Any, Dict, List, Optional
import requests

from .exceptions import (
    TossInvestError,
    BadRequestError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    UnprocessableEntityError,
    RateLimitError,
    ServerError,
)
from .models import (
    OAuth2TokenResponse,
    Account,
    HoldingsOverview,
    PriceResponse,
    OrderbookResponse,
    CandlePageResponse,
    StockInfo,
    StockWarning,
    Order,
    OrderOperationResponse,
    PaginatedOrderResponse,
)


class TossInvestClient:
    """A client for interacting with the Toss Securities Open API.

    This client automatically handles:
    - Token generation and caching (Client Credentials Grant)
    - Headers injection (Authorization and X-Tossinvest-Account)
    - Mapping HTTP error codes to meaningful Python exceptions
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "https://openapi.tossinvest.com",
        timeout: float = 10.0,
    ):
        """Initializes the TossInvestClient.

        Args:
            client_id: Toss Open API client ID.
            client_secret: Toss Open API client secret.
            base_url: Base URL of the API server (defaults to production URL).
            timeout: Default timeout in seconds for HTTP requests.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        self._token: Optional[str] = None
        self._token_expiry: Optional[float] = None

    def get_access_token(self) -> str:
        """Retrieves a cached OAuth2 access token or requests a new one if expired.

        Returns:
            The valid access token.
        """
        # If token exists and has not expired (with a 60-second safety buffer), return it
        if self._token and self._token_expiry and time.time() < self._token_expiry:
            return self._token

        url = f"{self.base_url}/oauth2/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        # Auth request uses application/x-www-form-urlencoded
        response = self.session.post(
            url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=self.timeout,
        )

        if response.status_code != 200:
            self._handle_error(response)

        data = response.json()
        token_resp = OAuth2TokenResponse.from_dict(data)

        self._token = token_resp.access_token
        # Cache token, expiring it 60 seconds earlier than the server limits for safety
        self._token_expiry = time.time() + token_resp.expires_in - 60
        return self._token

    def _request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Low-level request dispatcher that handles headers, auth, and error mapping."""
        url = f"{self.base_url}{path}"
        req_headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Accept": "application/json",
        }

        if headers:
            req_headers.update(headers)
        if account_seq is not None:
            req_headers["X-Tossinvest-Account"] = str(account_seq)

        response = self.session.request(
            method=method,
            url=url,
            headers=req_headers,
            params=params,
            json=json_data,
            timeout=self.timeout,
        )

        if not (200 <= response.status_code < 300):
            self._handle_error(response)

        return response.json()

    def _handle_error(self, response: requests.Response) -> None:
        """Parses error responses and raises corresponding custom exceptions."""
        status_code = response.status_code
        headers = response.headers

        try:
            err_json = response.json()
        except Exception:
            err_json = {}

        code = None
        message = response.text
        data = None
        request_id = headers.get("X-Request-Id")

        # Extract envelope fields
        if "error" in err_json:
            err_val = err_json["error"]
            if isinstance(err_val, dict):
                # Standard Toss API error envelope
                code = err_val.get("code")
                message = err_val.get("message", message)
                request_id = err_val.get("requestId", request_id)
                data = err_val.get("data")
            else:
                # OAuth2 error format (flat structure)
                code = err_val
                message = err_json.get("error_description", message)

        # Exception classification
        if status_code == 400:
            raise BadRequestError(message, code, request_id, data, status_code)
        elif status_code == 401:
            raise AuthenticationError(message, code, request_id, data, status_code)
        elif status_code == 403:
            raise ForbiddenError(message, code, request_id, data, status_code)
        elif status_code == 404:
            raise NotFoundError(message, code, request_id, data, status_code)
        elif status_code == 409:
            raise ConflictError(message, code, request_id, data, status_code)
        elif status_code == 422:
            raise UnprocessableEntityError(message, code, request_id, data, status_code)
        elif status_code == 429:
            retry_after = headers.get("Retry-After")
            retry_sec = int(retry_after) if retry_after and retry_after.isdigit() else None
            raise RateLimitError(
                message, code, request_id, data, status_code, retry_after=retry_sec
            )
        elif status_code >= 500:
            raise ServerError(message, code, request_id, data, status_code)
        else:
            raise TossInvestError(message, code, request_id, data, status_code)

    # --- Account APIs ---

    def get_accounts(self) -> List[Account]:
        """Retrieves list of brokerage accounts."""
        res = self._request("GET", "/api/v1/accounts")
        return [Account.from_dict(item) for item in res.get("result", [])]

    def get_holdings(self, account_seq: int, symbol: Optional[str] = None) -> HoldingsOverview:
        """Retrieves account stock holdings.

        Args:
            account_seq: The account identifier (accountSeq).
            symbol: If provided, filters results for the specified stock symbol.
        """
        params = {}
        if symbol:
            params["symbol"] = symbol

        res = self._request("GET", "/api/v1/holdings", params=params, account_seq=account_seq)
        return HoldingsOverview.from_dict(res.get("result", {}))

    # --- Market Data & Stock Info APIs ---

    def get_prices(self, symbols: List[str]) -> List[PriceResponse]:
        """Queries current prices for list of stock symbols (up to 200)."""
        params = {"symbols": ",".join(symbols)}
        res = self._request("GET", "/api/v1/prices", params=params)
        return [PriceResponse.from_dict(item) for item in res.get("result", [])]

    def get_orderbook(self, symbol: str) -> OrderbookResponse:
        """Queries current bids and asks for a single stock symbol."""
        params = {"symbol": symbol}
        res = self._request("GET", "/api/v1/orderbook", params=params)
        return OrderbookResponse.from_dict(res.get("result", {}))

    def get_candles(
        self,
        symbol: str,
        interval: str,
        count: Optional[int] = None,
        before: Optional[str] = None,
        adjusted: Optional[bool] = None,
    ) -> CandlePageResponse:
        """Queries OHLCV candle chart data.

        Args:
            symbol: Stock symbol.
            interval: Bar interval ('1m' or '1d').
            count: Number of bars to return (up to 200).
            before: Pagination upper limit (exclusive ISO 8601 date string).
            adjusted: Whether to apply split/dividend adjustments.
        """
        params = {"symbol": symbol, "interval": interval}
        if count is not None:
            params["count"] = count
        if before is not None:
            params["before"] = before
        if adjusted is not None:
            params["adjusted"] = str(adjusted).lower()

        res = self._request("GET", "/api/v1/candles", params=params)
        return CandlePageResponse.from_dict(res.get("result", {}))

    def get_stocks(self, symbols: List[str]) -> List[StockInfo]:
        """Queries stock master metadata for list of stock symbols (up to 200)."""
        params = {"symbols": ",".join(symbols)}
        res = self._request("GET", "/api/v1/stocks", params=params)
        return [StockInfo.from_dict(item) for item in res.get("result", [])]

    def get_stock_warnings(self, symbol: str) -> List[StockWarning]:
        """Queries active stock warnings and trading restrictions."""
        res = self._request("GET", f"/api/v1/stocks/{symbol}/warnings")
        return [StockWarning.from_dict(item) for item in res.get("result", [])]

    # --- Trading (Order) APIs ---

    def create_order(
        self,
        account_seq: int,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        order_amount: Optional[float] = None,
        client_order_id: Optional[str] = None,
        time_in_force: Optional[str] = None,
        confirm_high_value_order: Optional[bool] = None,
    ) -> OrderOperationResponse:
        """Creates a new buying or selling order.

        Exactly one of `quantity` or `order_amount` (US market-only) must be provided.
        """
        body: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
        }
        if quantity is not None:
            body["quantity"] = quantity
        if price is not None:
            body["price"] = price
        if order_amount is not None:
            body["orderAmount"] = order_amount
        if client_order_id is not None:
            body["clientOrderId"] = client_order_id
        if time_in_force is not None:
            body["timeInForce"] = time_in_force
        if confirm_high_value_order is not None:
            body["confirmHighValueOrder"] = confirm_high_value_order

        res = self._request("POST", "/api/v1/orders", json_data=body, account_seq=account_seq)
        return OrderOperationResponse.from_dict(res.get("result", {}))

    def modify_order(
        self,
        account_seq: int,
        order_id: str,
        order_type: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        confirm_high_value_order: Optional[bool] = None,
    ) -> OrderOperationResponse:
        """Modifies price and/or quantity of an open order."""
        body: Dict[str, Any] = {
            "orderType": order_type,
        }
        if quantity is not None:
            body["quantity"] = quantity
        if price is not None:
            body["price"] = price
        if confirm_high_value_order is not None:
            body["confirmHighValueOrder"] = confirm_high_value_order

        res = self._request(
            "POST", f"/api/v1/orders/{order_id}/modify", json_data=body, account_seq=account_seq
        )
        return OrderOperationResponse.from_dict(res.get("result", {}))

    def cancel_order(self, account_seq: int, order_id: str) -> OrderOperationResponse:
        """Cancels an open order."""
        res = self._request(
            "POST", f"/api/v1/orders/{order_id}/cancel", json_data={}, account_seq=account_seq
        )
        return OrderOperationResponse.from_dict(res.get("result", {}))

    def get_order(self, account_seq: int, order_id: str) -> Order:
        """Retrieves full details of a specific order."""
        res = self._request("GET", f"/api/v1/orders/{order_id}", account_seq=account_seq)
        return Order.from_dict(res.get("result", {}))

    def get_orders(
        self,
        account_seq: int,
        status: str,
        symbol: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> PaginatedOrderResponse:
        """Retrieves list of orders matching filters.

        Args:
            account_seq: The account identifier.
            status: Status group filter ('OPEN' or 'CLOSED').
            symbol: Optional stock symbol.
            from_date: Optional start date filter (inclusive YYYY-MM-DD KST).
            to_date: Optional end date filter (inclusive YYYY-MM-DD KST).
            cursor: Pagination cursor (used for CLOSED status).
            limit: Page size limit (defaults to 20, max 100, used for CLOSED status).
        """
        params: Dict[str, Any] = {"status": status}
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

        res = self._request("GET", "/api/v1/orders", params=params, account_seq=account_seq)
        return PaginatedOrderResponse.from_dict(res.get("result", {}))
