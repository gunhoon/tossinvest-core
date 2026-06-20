import pytest
from unittest.mock import patch, MagicMock
import time

from tossinvest import TossInvestClient

@pytest.fixture
def client():
    c = TossInvestClient(
        client_id="id",
        client_secret="secret",
        base_url="https://openapi.test.com",
        account_seq=123,
    )
    # Pre-cache token to avoid authentication calls during service tests
    c._access_token = "mock_token"
    c._token_expires_at = time.time() + 1000
    return c

@patch("requests.Session.request")
def test_market_service(mock_request, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"mock": "data"}
    mock_request.return_value = mock_response

    # Test get_prices with list
    client.market.get_prices(["005930", "000660"])
    mock_request.assert_called_with(
        "GET",
        "https://openapi.test.com/api/v1/prices",
        headers={"Authorization": "Bearer mock_token"},
        params={"symbols": "005930,000660"},
    )

    # Test get_candles
    client.market.get_candles("005930", "1d", count=10, adjusted=True)
    mock_request.assert_called_with(
        "GET",
        "https://openapi.test.com/api/v1/candles",
        headers={"Authorization": "Bearer mock_token"},
        params={"symbol": "005930", "interval": "1d", "count": 10, "adjusted": True},
    )

    # Test get_exchange_rate (converting snake_case arguments to camelCase API parameters)
    client.market.get_exchange_rate(base_currency="USD", quote_currency="KRW", date_time="2026-06-20T12:00:00Z")
    mock_request.assert_called_with(
        "GET",
        "https://openapi.test.com/api/v1/exchange-rate",
        headers={"Authorization": "Bearer mock_token"},
        params={"baseCurrency": "USD", "quoteCurrency": "KRW", "dateTime": "2026-06-20T12:00:00Z"},
    )

@patch("requests.Session.request")
def test_account_service(mock_request, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"mock": "data"}
    mock_request.return_value = mock_response

    # Test get_accounts - shouldn't have X-Tossinvest-Account header
    client.account.get_accounts()
    mock_request.assert_called_with(
        "GET",
        "https://openapi.test.com/api/v1/accounts",
        headers={"Authorization": "Bearer mock_token"},
        params=None,
    )

    # Test get_holdings - should have X-Tossinvest-Account header from client default
    client.account.get_holdings(symbol="005930")
    mock_request.assert_called_with(
        "GET",
        "https://openapi.test.com/api/v1/holdings",
        headers={
            "Authorization": "Bearer mock_token",
            "X-Tossinvest-Account": "123"
        },
        params={"symbol": "005930"},
    )

    # Test get_holdings - override account_seq
    client.account.get_holdings(account_seq=456)
    mock_request.assert_called_with(
        "GET",
        "https://openapi.test.com/api/v1/holdings",
        headers={
            "Authorization": "Bearer mock_token",
            "X-Tossinvest-Account": "456"
        },
        params={},
    )

@patch("requests.Session.request")
def test_order_service_placement(mock_request, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"orderId": "ord_999"}
    mock_request.return_value = mock_response

    # Test create_quantity_order (testing type string conversions for quantity/price)
    client.order.create_quantity_order(
        symbol="005930",
        side="buy",
        order_type="limit",
        quantity=10,
        price=72000,
        confirm_high_value_order=True,
    )
    mock_request.assert_called_with(
        "POST",
        "https://openapi.test.com/api/v1/orders",
        headers={
            "Authorization": "Bearer mock_token",
            "X-Tossinvest-Account": "123",
        },
        params=None,
        json={
            "symbol": "005930",
            "side": "BUY",
            "orderType": "LIMIT",
            "quantity": "10",
            "price": "72000",
            "confirmHighValueOrder": True,
        }
    )

    # Test create_amount_order (fractional shares USD)
    client.order.create_amount_order(
        symbol="AAPL",
        side="sell",
        order_amount=150.50,
        client_order_id="client_id_001",
    )
    mock_request.assert_called_with(
        "POST",
        "https://openapi.test.com/api/v1/orders",
        headers={
            "Authorization": "Bearer mock_token",
            "X-Tossinvest-Account": "123",
        },
        params=None,
        json={
            "symbol": "AAPL",
            "side": "SELL",
            "orderType": "MARKET",
            "orderAmount": "150.5",
            "confirmHighValueOrder": False,
            "clientOrderId": "client_id_001",
        }
    )

@patch("requests.Session.request")
def test_order_service_actions_and_queries(mock_request, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"mock": "data"}
    mock_request.return_value = mock_response

    # Test cancel_order (sends empty dict json={})
    client.order.cancel_order("ord_999")
    mock_request.assert_called_with(
        "POST",
        "https://openapi.test.com/api/v1/orders/ord_999/cancel",
        headers={
            "Authorization": "Bearer mock_token",
            "X-Tossinvest-Account": "123",
        },
        params=None,
        json={},
    )

    # Test get_orders (mapping reserved from_date to "from", and to_date to "to")
    client.order.get_orders(
        status="closed",
        from_date="2026-06-01",
        to_date="2026-06-20",
        limit=50,
    )
    mock_request.assert_called_with(
        "GET",
        "https://openapi.test.com/api/v1/orders",
        headers={
            "Authorization": "Bearer mock_token",
            "X-Tossinvest-Account": "123",
        },
        params={
            "status": "CLOSED",
            "from": "2026-06-01",
            "to": "2026-06-20",
            "limit": 50,
        },
    )
