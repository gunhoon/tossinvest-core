import time
import pytest
import responses
from unittest.mock import patch

from tossinvest.client import TossInvestClient
from tossinvest.exceptions import (
    BadRequestError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from tossinvest.models import (
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


@responses.activate
def test_get_access_token_success(mock_client):
    # Mock token response
    responses.add(
        responses.POST,
        "https://openapi.tossinvest.com/oauth2/token",
        json={
            "access_token": "mocked_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
        status=200,
    )

    token = mock_client.get_access_token()
    assert token == "mocked_access_token"
    assert mock_client._token == "mocked_access_token"
    assert mock_client._token_expiry is not None

    # Calling again should use cache (responses has no more mock setups, so it would error if requested)
    cached_token = mock_client.get_access_token()
    assert cached_token == "mocked_access_token"


@responses.activate
def test_get_access_token_expired(mock_client):
    # Setup token and expire it manually
    mock_client._token = "old_token"
    mock_client._token_expiry = time.time() - 10  # expired

    # Mock new token response
    responses.add(
        responses.POST,
        "https://openapi.tossinvest.com/oauth2/token",
        json={
            "access_token": "new_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
        status=200,
    )

    token = mock_client.get_access_token()
    assert token == "new_token"


@responses.activate
def test_error_handling_invalid_request(mock_client):
    # Mock token first
    mock_client._token = "mocked_access_token"
    mock_client._token_expiry = time.time() + 1000

    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/accounts",
        json={
            "error": {
                "requestId": "req_123",
                "code": "invalid-request",
                "message": "요청이 유효하지 않습니다.",
                "data": {"field": "side"},
            }
        },
        status=400,
    )

    with pytest.raises(BadRequestError) as exc_info:
        mock_client.get_accounts()

    assert exc_info.value.code == "invalid-request"
    assert exc_info.value.request_id == "req_123"
    assert exc_info.value.data == {"field": "side"}
    assert "요청이 유효하지 않습니다." in str(exc_info.value)


@responses.activate
def test_error_handling_rate_limit(mock_client):
    mock_client._token = "mocked_access_token"
    mock_client._token_expiry = time.time() + 1000

    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/accounts",
        json={
            "error": {
                "code": "rate-limit-exceeded",
                "message": "Rate limit exceeded.",
            }
        },
        headers={"Retry-After": "5"},
        status=429,
    )

    with pytest.raises(RateLimitError) as exc_info:
        mock_client.get_accounts()

    assert exc_info.value.retry_after == 5
    assert "Retry-After: 5s" in str(exc_info.value)


@responses.activate
def test_get_accounts(mock_client):
    mock_client._token = "mocked_access_token"
    mock_client._token_expiry = time.time() + 1000

    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/accounts",
        json={
            "result": [
                {
                    "accountNo": "123-456-789",
                    "accountSeq": 1,
                    "accountType": "BROKERAGE",
                }
            ]
        },
        status=200,
    )

    accounts = mock_client.get_accounts()
    assert len(accounts) == 1
    assert isinstance(accounts[0], Account)
    assert accounts[0].accountNo == "123-456-789"
    assert accounts[0].accountSeq == 1


@responses.activate
def test_get_holdings(mock_client):
    mock_client._token = "mocked_access_token"
    mock_client._token_expiry = time.time() + 1000

    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/holdings",
        json={
            "result": {
                "totalPurchaseAmount": {"krw": 10000, "usd": 10},
                "marketValue": {"krw": 12000, "usd": 12},
                "profitLoss": {"krw": 2000, "usd": 2, "rate": 0.2},
                "dailyProfitLoss": {"krw": 500, "usd": 0.5, "rate": 0.05},
                "items": [
                    {
                        "symbol": "005930",
                        "name": "삼성전자",
                        "marketCountry": "KR",
                        "currency": "KRW",
                        "quantity": 10,
                        "lastPrice": 70000,
                        "averagePurchasePrice": 65000,
                        "marketValue": {"krw": 700000},
                        "profitLoss": {"krw": 50000, "rate": 0.0769},
                        "dailyProfitLoss": {"krw": 10000, "rate": 0.0145},
                        "cost": {"krw": 650000},
                    }
                ],
            }
        },
        status=200,
    )

    holdings = mock_client.get_holdings(account_seq=1, symbol="005930")
    assert isinstance(holdings, HoldingsOverview)
    assert holdings.totalPurchaseAmount.krw == 10000
    assert holdings.totalPurchaseAmount.usd == 10
    assert len(holdings.items) == 1
    assert holdings.items[0].symbol == "005930"
    assert holdings.items[0].quantity == 10.0


@responses.activate
def test_get_prices(mock_client):
    mock_client._token = "mocked_access_token"
    mock_client._token_expiry = time.time() + 1000

    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/prices",
        json={
            "result": [
                {
                    "symbol": "005930",
                    "lastPrice": 72000,
                    "currency": "KRW",
                    "timestamp": "2026-06-20T13:40:00+09:00",
                }
            ]
        },
        status=200,
    )

    prices = mock_client.get_prices(["005930"])
    assert len(prices) == 1
    assert isinstance(prices[0], PriceResponse)
    assert prices[0].symbol == "005930"
    assert prices[0].lastPrice == 72000


@responses.activate
def test_get_orderbook(mock_client):
    mock_client._token = "mocked_access_token"
    mock_client._token_expiry = time.time() + 1000

    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/orderbook",
        json={
            "result": {
                "currency": "KRW",
                "asks": [{"price": 72100, "volume": 100}],
                "bids": [{"price": 72000, "volume": 150}],
                "timestamp": "2026-06-20T13:40:00+09:00",
            }
        },
        status=200,
    )

    ob = mock_client.get_orderbook("005930")
    assert isinstance(ob, OrderbookResponse)
    assert ob.currency == "KRW"
    assert ob.asks[0].price == 72100
    assert ob.bids[0].volume == 150


@responses.activate
def test_get_candles(mock_client):
    mock_client._token = "mocked_access_token"
    mock_client._token_expiry = time.time() + 1000

    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/candles",
        json={
            "result": {
                "candles": [
                    {
                        "timestamp": "2026-06-20T13:40:00+09:00",
                        "openPrice": 72000,
                        "highPrice": 72500,
                        "lowPrice": 71900,
                        "closePrice": 72200,
                        "volume": 50000,
                        "currency": "KRW",
                    }
                ],
                "nextBefore": "2026-06-20T13:39:00+09:00",
            }
        },
        status=200,
    )

    res = mock_client.get_candles("005930", interval="1m", count=1)
    assert isinstance(res, CandlePageResponse)
    assert len(res.candles) == 1
    assert res.candles[0].closePrice == 72200
    assert res.nextBefore == "2026-06-20T13:39:00+09:00"


@responses.activate
def test_get_stocks(mock_client):
    mock_client._token = "mocked_access_token"
    mock_client._token_expiry = time.time() + 1000

    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/stocks",
        json={
            "result": [
                {
                    "symbol": "005930",
                    "name": "삼성전자",
                    "englishName": "Samsung Electronics",
                    "isinCode": "KR7005930003",
                    "market": "KOSPI",
                    "securityType": "COMMON_STOCK",
                    "isCommonShare": True,
                    "status": "LISTED",
                    "currency": "KRW",
                    "sharesOutstanding": 5969782550,
                }
            ]
        },
        status=200,
    )

    info = mock_client.get_stocks(["005930"])
    assert len(info) == 1
    assert isinstance(info[0], StockInfo)
    assert info[0].name == "삼성전자"
    assert info[0].isCommonShare is True


@responses.activate
def test_get_stock_warnings(mock_client):
    mock_client._token = "mocked_access_token"
    mock_client._token_expiry = time.time() + 1000

    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/stocks/005930/warnings",
        json={
            "result": [
                {
                    "warningType": "OVERHEATED",
                    "startDate": "2026-06-19",
                    "endDate": "2026-06-21",
                    "exchange": "KRX",
                }
            ]
        },
        status=200,
    )

    warnings = mock_client.get_stock_warnings("005930")
    assert len(warnings) == 1
    assert isinstance(warnings[0], StockWarning)
    assert warnings[0].warningType == "OVERHEATED"


@responses.activate
def test_create_order(mock_client):
    mock_client._token = "mocked_access_token"
    mock_client._token_expiry = time.time() + 1000

    responses.add(
        responses.POST,
        "https://openapi.tossinvest.com/api/v1/orders",
        json={"result": {"orderId": "order_uuid_111"}},
        status=200,
    )

    res = mock_client.create_order(
        account_seq=1,
        symbol="005930",
        side="BUY",
        order_type="LIMIT",
        quantity=10,
        price=70000,
    )

    assert isinstance(res, OrderOperationResponse)
    assert res.orderId == "order_uuid_111"


@responses.activate
def test_modify_order(mock_client):
    mock_client._token = "mocked_access_token"
    mock_client._token_expiry = time.time() + 1000

    responses.add(
        responses.POST,
        "https://openapi.tossinvest.com/api/v1/orders/order_uuid_111/modify",
        json={"result": {"orderId": "order_uuid_111"}},
        status=200,
    )

    res = mock_client.modify_order(
        account_seq=1,
        order_id="order_uuid_111",
        order_type="LIMIT",
        quantity=5,
        price=71000,
    )

    assert res.orderId == "order_uuid_111"


@responses.activate
def test_cancel_order(mock_client):
    mock_client._token = "mocked_access_token"
    mock_client._token_expiry = time.time() + 1000

    responses.add(
        responses.POST,
        "https://openapi.tossinvest.com/api/v1/orders/order_uuid_111/cancel",
        json={"result": {"orderId": "order_uuid_111"}},
        status=200,
    )

    res = mock_client.cancel_order(account_seq=1, order_id="order_uuid_111")
    assert res.orderId == "order_uuid_111"


@responses.activate
def test_get_order(mock_client):
    mock_client._token = "mocked_access_token"
    mock_client._token_expiry = time.time() + 1000

    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/orders/order_uuid_111",
        json={
            "result": {
                "orderId": "order_uuid_111",
                "symbol": "005930",
                "side": "BUY",
                "orderType": "LIMIT",
                "timeInForce": "DAY",
                "status": "PENDING",
                "price": 70000,
                "quantity": 10,
                "currency": "KRW",
                "orderedAt": "2026-06-20T13:40:00+09:00",
                "execution": {
                    "filledQuantity": 0,
                },
            }
        },
        status=200,
    )

    order = mock_client.get_order(account_seq=1, order_id="order_uuid_111")
    assert isinstance(order, Order)
    assert order.orderId == "order_uuid_111"
    assert order.execution.filledQuantity == 0.0


@responses.activate
def test_get_orders(mock_client):
    mock_client._token = "mocked_access_token"
    mock_client._token_expiry = time.time() + 1000

    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/orders",
        json={
            "result": {
                "orders": [
                    {
                        "orderId": "order_uuid_111",
                        "symbol": "005930",
                        "side": "BUY",
                        "orderType": "LIMIT",
                        "timeInForce": "DAY",
                        "status": "PENDING",
                        "price": 70000,
                        "quantity": 10,
                        "currency": "KRW",
                        "orderedAt": "2026-06-20T13:40:00+09:00",
                        "execution": {"filledQuantity": 0},
                    }
                ],
                "hasNext": False,
                "nextCursor": None,
            }
        },
        status=200,
    )

    res = mock_client.get_orders(account_seq=1, status="OPEN")
    assert isinstance(res, PaginatedOrderResponse)
    assert len(res.orders) == 1
    assert res.orders[0].orderId == "order_uuid_111"
    assert res.hasNext is False
