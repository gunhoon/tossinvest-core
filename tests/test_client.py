import pytest
from unittest.mock import patch, MagicMock
import time

from tossinvest import (
    TossInvestClient,
    AuthenticationError,
    RateLimitExceeded,
)

@pytest.fixture
def client():
    return TossInvestClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
        base_url="https://openapi.test.com",
        account_seq=999,
    )

@patch("requests.Session.request")
def test_token_caching_and_expiration(mock_request, client):
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
    token = client.auth.get_token()
    assert token == "token_123"
    assert mock_request.call_count == 1

    # 3. Second call should return cached token without requesting
    token_cached = client.auth.get_token()
    assert token_cached == "token_123"
    assert mock_request.call_count == 1

    # 4. Mock expiration (fast-forward time)
    client._token_expires_at = time.time() - 10
    mock_response.json.return_value = {
        "access_token": "token_456",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    token_refreshed = client.auth.get_token()
    assert token_refreshed == "token_456"
    assert mock_request.call_count == 2

@patch("requests.Session.request")
def test_auto_retry_on_401_expired_token(mock_request, client):
    # Setup cached token
    client._access_token = "expired_token"
    client._token_expires_at = time.time() + 1000

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
    result = client.market.get_orderbook("005930")
    assert result == {"data": "success"}
    assert client._access_token == "new_token"
    assert mock_request.call_count == 3

@patch("time.sleep")
@patch("requests.Session.request")
def test_auto_retry_on_429_rate_limit(mock_request, mock_sleep, client):
    # Setup cached token
    client._access_token = "valid_token"
    client._token_expires_at = time.time() + 1000

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

    result = client.market.get_orderbook("005930")
    assert result == {"status": "ok"}
    mock_sleep.assert_called_once_with(2.5)
    assert client.rate_limit_info["limit"] == 10

@patch("time.sleep")
@patch("requests.Session.request")
def test_429_exceeds_max_retries(mock_request, mock_sleep, client):
    client._access_token = "valid_token"
    client._token_expires_at = time.time() + 1000

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

    with pytest.raises(RateLimitExceeded):
        client.market.get_orderbook("005930")
        
    assert mock_sleep.call_count == 3
