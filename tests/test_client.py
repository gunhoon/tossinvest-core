import unittest
from unittest.mock import MagicMock, patch

from tossinvest import (
    TossInvestAPIError,
    TossInvestAuthError,
    TossInvestClient,
    TossInvestError,
    TossInvestRateLimitError,
)


class TestTossInvestClient(unittest.TestCase):

    def setUp(self):
        self.client_id = "test-client-id"
        self.client_secret = "test-client-secret"
        self.client = TossInvestClient(
            client_id=self.client_id,
            client_secret=self.client_secret,
            account_seq=12345,
        )

    @patch("time.time")
    def test_token_caching_and_refresh(self, mock_time):
        # Initial call: Token is requested
        mock_time.return_value = 1000.0

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "token-1",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        with patch.object(self.client.session, "post", return_value=mock_response) as mock_post:
            token = self.client._get_valid_token()
            self.assertEqual(token, "token-1")
            self.assertEqual(self.client._token, "token-1")
            self.assertEqual(self.client._token_expires_at, 4600.0)
            mock_post.assert_called_once()

        # Second call: Token is still valid (cached), post is not called
        mock_time.return_value = 2000.0  # Still before 4540 (4600 - 60 safety buffer)
        with patch.object(self.client.session, "post") as mock_post:
            token = self.client._get_valid_token()
            self.assertEqual(token, "token-1")
            mock_post.assert_not_called()

        # Third call: Token expired (or within safety buffer), post is called to refresh
        mock_time.return_value = 4550.0  # within 60s of expiration
        mock_response_2 = MagicMock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = {
            "access_token": "token-2",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        with patch.object(self.client.session, "post", return_value=mock_response_2) as mock_post:
            token = self.client._get_valid_token()
            self.assertEqual(token, "token-2")
            mock_post.assert_called_once()

    def test_auth_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid credentials"

        with patch.object(self.client.session, "post", return_value=mock_response):
            with self.assertRaises(TossInvestAuthError) as ctx:
                self.client.issue_token()
            self.assertIn("Authentication failed", str(ctx.exception))
            self.assertEqual(ctx.exception.response_body, "Invalid credentials")

    @patch.object(TossInvestClient, "_get_valid_token", return_value="mock-token")
    def test_request_success_unwraps_result(self, mock_token):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {"some_key": "some_value"}}

        with patch.object(self.client.session, "request", return_value=mock_response) as mock_req:
            res = self.client._request("GET", "/api/v1/some-endpoint")
            self.assertEqual(res, {"some_key": "some_value"})
            mock_req.assert_called_once()

    @patch.object(TossInvestClient, "_get_valid_token", return_value="mock-token")
    def test_api_error_raised(self, mock_token):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.headers = {"X-Request-Id": "req-123"}
        mock_response.json.return_value = {
            "error": {
                "requestId": "req-123",
                "code": "invalid-request",
                "message": "Bad request body",
                "data": {"field": "quantity"},
            }
        }

        with patch.object(self.client.session, "request", return_value=mock_response):
            with self.assertRaises(TossInvestAPIError) as ctx:
                self.client._request("GET", "/api/v1/some-endpoint")
            err = ctx.exception
            self.assertEqual(err.status_code, 400)
            self.assertEqual(err.request_id, "req-123")
            self.assertEqual(err.code, "invalid-request")
            self.assertEqual(err.message, "Bad request body")
            self.assertEqual(err.data, {"field": "quantity"})

    @patch("time.sleep")
    @patch.object(TossInvestClient, "_get_valid_token", return_value="mock-token")
    def test_rate_limit_error_raised(self, mock_token, mock_sleep):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"X-Request-Id": "req-123", "Retry-After": "5"}
        mock_response.json.return_value = {
            "error": {
                "code": "rate-limit-exceeded",
                "message": "Too many requests",
            }
        }

        with patch.object(self.client.session, "request", return_value=mock_response) as mock_req:
            with self.assertRaises(TossInvestRateLimitError) as ctx:
                self.client._request("GET", "/api/v1/some-endpoint")
            err = ctx.exception
            self.assertEqual(err.status_code, 429)
            self.assertEqual(err.retry_after_seconds, 5)
            self.assertEqual(mock_req.call_count, 4)
            self.assertEqual(mock_sleep.call_count, 3)
            mock_sleep.assert_has_calls([unittest.mock.call(5)] * 3)

    @patch("time.sleep")
    @patch.object(TossInvestClient, "_get_valid_token", return_value="mock-token")
    def test_rate_limit_retry_success(self, mock_token, mock_sleep):
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {"Retry-After": "3"}
        mock_429.json.return_value = {
            "error": {
                "code": "rate-limit-exceeded",
                "message": "Too many requests",
            }
        }

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = {"result": {"success": True}}

        with patch.object(self.client.session, "request", side_effect=[mock_429, mock_200]) as mock_req:
            res = self.client._request("GET", "/api/v1/some-endpoint")
            self.assertEqual(res, {"success": True})
            self.assertEqual(mock_req.call_count, 2)
            mock_sleep.assert_called_once_with(3)

    @patch.object(TossInvestClient, "_request")
    def test_market_data_endpoints(self, mock_request):
        # 1. get_prices
        self.client.market.get_prices(["005930", "AAPL"])
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/prices",
            params={"symbols": "005930,AAPL"},
        )

        # 2. get_orderbook
        self.client.market.get_orderbook("005930")
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/orderbook",
            params={"symbol": "005930"},
        )

        # 3. get_candles
        self.client.market.get_candles("005930", "1d", count=50, adjusted=False)
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/candles",
            params={"symbol": "005930", "interval": "1d", "count": 50, "adjusted": "false"},
        )

        # 4. get_price_limits
        self.client.market.get_price_limits("005930")
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/price-limits",
            params={"symbol": "005930"},
        )

        # 5. get_trades
        self.client.market.get_trades("005930", count=20)
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/trades",
            params={"symbol": "005930", "count": 20},
        )

    @patch.object(TossInvestClient, "_request")
    def test_stock_info_endpoints(self, mock_request):
        # get_stocks
        self.client.market.get_stocks(["005930"])
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/stocks",
            params={"symbols": "005930"},
        )

        # get_stock_warnings
        self.client.market.get_stock_warnings("005930")
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/stocks/005930/warnings",
        )

        # get_exchange_rate
        self.client.market.get_exchange_rate(base_currency="USD", quote_currency="KRW")
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/exchange-rate",
            params={"baseCurrency": "USD", "quoteCurrency": "KRW"},
        )

        # get_market_calendar
        self.client.market.get_market_calendar(country="KR", date="2026-06-20")
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/market-calendar/KR",
            params={"date": "2026-06-20"},
        )

    @patch.object(TossInvestClient, "_request")
    def test_account_and_asset_endpoints(self, mock_request):
        # get_accounts (requires auth, but not account header)
        self.client.account.get_accounts()
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/accounts",
            requires_auth=True,
            requires_account=False,
        )

        # get_holdings (requires auth, and account header)
        self.client.account.get_holdings(symbol="005930")
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/holdings",
            params={"symbol": "005930"},
            requires_auth=True,
            requires_account=True,
            account_seq=None,
        )

    @patch.object(TossInvestClient, "_request")
    def test_order_endpoints(self, mock_request):
        # create_order
        self.client.order.create_order(
            symbol="005930",
            side="BUY",
            order_type="LIMIT",
            quantity="10",
            price="70000",
            client_order_id="id-001",
        )
        mock_request.assert_called_with(
            method="POST",
            path="/api/v1/orders",
            json={
                "symbol": "005930",
                "side": "BUY",
                "orderType": "LIMIT",
                "timeInForce": "DAY",
                "confirmHighValueOrder": False,
                "quantity": "10",
                "price": "70000",
                "clientOrderId": "id-001",
            },
            requires_auth=True,
            requires_account=True,
            account_seq=None,
        )

        # modify_order
        self.client.order.modify_order(
            order_id="ord-abc",
            order_type="LIMIT",
            price="71000",
            quantity="15",
        )
        mock_request.assert_called_with(
            method="POST",
            path="/api/v1/orders/ord-abc/modify",
            json={
                "orderType": "LIMIT",
                "confirmHighValueOrder": False,
                "price": "71000",
                "quantity": "15",
            },
            requires_auth=True,
            requires_account=True,
            account_seq=None,
        )

        # cancel_order
        self.client.order.cancel_order(order_id="ord-abc")
        mock_request.assert_called_with(
            method="POST",
            path="/api/v1/orders/ord-abc/cancel",
            json={},
            requires_auth=True,
            requires_account=True,
            account_seq=None,
        )

        # get_orders
        self.client.order.get_orders(status="OPEN", symbol="005930")
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/orders",
            params={"status": "OPEN", "symbol": "005930"},
            requires_auth=True,
            requires_account=True,
            account_seq=None,
        )

        # get_order_detail
        self.client.order.get_order_detail(order_id="ord-abc")
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/orders/ord-abc",
            requires_auth=True,
            requires_account=True,
            account_seq=None,
        )

        # get_buying_power
        self.client.order.get_buying_power(currency="KRW")
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/buying-power",
            params={"currency": "KRW"},
            requires_auth=True,
            requires_account=True,
            account_seq=None,
        )

        # get_sellable_quantity
        self.client.order.get_sellable_quantity(symbol="005930")
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/sellable-quantity",
            params={"symbol": "005930"},
            requires_auth=True,
            requires_account=True,
            account_seq=None,
        )

        # get_commissions
        self.client.order.get_commissions()
        mock_request.assert_called_with(
            method="GET",
            path="/api/v1/commissions",
            requires_auth=True,
            requires_account=True,
            account_seq=None,
        )


if __name__ == "__main__":
    unittest.main()
