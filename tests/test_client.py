import unittest
from unittest.mock import patch, MagicMock
import time

from tossinvest import (
    TossInvestClient,
    AuthenticationError,
    RateLimitExceeded,
    InvalidRequestError,
)

class TestTossInvestClient(unittest.TestCase):
    def setUp(self):
        self.client_id = "test_client_id"
        self.client_secret = "test_client_secret"
        self.client = TossInvestClient(
            client_id=self.client_id,
            client_secret=self.client_secret,
            base_url="https://openapi.test.com",
            account_seq=999,
        )

    @patch("requests.Session.request")
    def test_token_caching_and_expiration(self, mock_request):
        # 1. Mock token response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {
            "access_token": "token_123",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_request.return_value = mock_response

        # 2. First call should request token
        token = self.client.auth.get_token()
        self.assertEqual(token, "token_123")
        self.assertEqual(mock_request.call_count, 1)

        # 3. Second call should return cached token without requesting
        token_cached = self.client.auth.get_token()
        self.assertEqual(token_cached, "token_123")
        self.assertEqual(mock_request.call_count, 1)

        # 4. Mock expiration (fast-forward time)
        self.client._token_expires_at = time.time() - 10
        mock_response.json.return_value = {
            "access_token": "token_456",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        token_refreshed = self.client.auth.get_token()
        self.assertEqual(token_refreshed, "token_456")
        self.assertEqual(mock_request.call_count, 2)

    @patch("requests.Session.request")
    def test_auto_retry_on_401_expired_token(self, mock_request):
        # Setup cached token
        self.client._access_token = "expired_token"
        self.client._token_expires_at = time.time() + 1000

        # Mock first call returns 401 expired-token
        response_401 = MagicMock()
        response_401.status_code = 401
        response_401.headers = {}
        response_401.json.return_value = {
            "error": {
                "requestId": "req1",
                "code": "expired-token",
                "message": "Token expired"
            }
        }

        # Mock token refresh call
        response_token = MagicMock()
        response_token.status_code = 200
        response_token.headers = {}
        response_token.json.return_value = {
            "access_token": "new_token",
            "expires_in": 3600
        }

        # Mock second attempt success
        response_success = MagicMock()
        response_success.status_code = 200
        response_success.headers = {}
        response_success.json.return_value = {"data": "success"}

        mock_request.side_effect = [response_401, response_token, response_success]

        # Call market API (which uses auth)
        result = self.client.market.get_orderbook("005930")
        self.assertEqual(result, {"data": "success"})
        self.assertEqual(self.client._access_token, "new_token")
        self.assertEqual(mock_request.call_count, 3)

    @patch("time.sleep")
    @patch("requests.Session.request")
    def test_auto_retry_on_429_rate_limit(self, mock_request, mock_sleep):
        # Setup cached token to bypass auth request in test
        self.client._access_token = "valid_token"
        self.client._token_expires_at = time.time() + 1000

        response_429 = MagicMock()
        response_429.status_code = 429
        response_429.headers = {"Retry-After": "2.5"}
        response_429.json.return_value = {
            "error": {
                "code": "rate-limit-exceeded",
                "message": "Too many requests"
            }
        }

        response_success = MagicMock()
        response_success.status_code = 200
        response_success.headers = {"X-RateLimit-Limit": "10"}
        response_success.json.return_value = {"status": "ok"}

        mock_request.side_effect = [response_429, response_success]

        result = self.client.market.get_orderbook("005930")
        self.assertEqual(result, {"status": "ok"})
        mock_sleep.assert_called_once_with(2.5)
        self.assertEqual(self.client.rate_limit_info["limit"], 10)

    @patch("time.sleep")
    @patch("requests.Session.request")
    def test_429_exceeds_max_retries(self, mock_request, mock_sleep):
        self.client._access_token = "valid_token"
        self.client._token_expires_at = time.time() + 1000

        response_429 = MagicMock()
        response_429.status_code = 429
        response_429.headers = {"Retry-After": "1.0"}
        response_429.json.return_value = {
            "error": {
                "code": "rate-limit-exceeded",
                "message": "Too many requests"
            }
        }

        mock_request.return_value = response_429

        with self.assertRaises(RateLimitExceeded):
            self.client.market.get_orderbook("005930")
            
        self.assertEqual(mock_sleep.call_count, 3) # Max retries is 3
