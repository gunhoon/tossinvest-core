import time
import pytest
import responses

from tossinvest import (
    TossInvestClient,
    TossInvestError,
    TossInvestAPIError,
    TossInvestAuthError,
)
from tossinvest.models import (
    TokenInfo,
    PriceResponse,
    OrderbookResponse,
    Trade,
    PriceLimitResponse,
    CandlePageResponse,
    StockInfo,
    StockWarning,
    ExchangeRateResponse,
    KrMarketDay,
    UsMarketDay,
    Account,
    HoldingsOverview,
    BuyingPowerResponse,
    SellableQuantityResponse,
    Commission,
    Order,
    OrderResponse,
    PaginatedOrderResponse,
)


@pytest.fixture
def client():
    # Setup client with mock credentials
    return TossInvestClient(
        client_id="mock_client_id",
        client_secret="mock_client_secret",
        base_url="https://openapi.tossinvest.com",
    )


def mock_token_response(rsps, expires_in=3600):
    rsps.add(
        responses.POST,
        "https://openapi.tossinvest.com/oauth2/token",
        json={
            "access_token": "mock_jwt_token",
            "token_type": "Bearer",
            "expires_in": expires_in,
        },
        status=200,
    )


@responses.activate
def test_token_issuance_and_caching(client):
    mock_token_response(responses)
    
    # Mock some endpoint to trigger token retrieval
    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/orderbook",
        json={"result": {"timestamp": "2026-03-25T09:30:00+09:00", "currency": "KRW", "asks": [], "bids": []}},
        status=200,
    )
    
    # Retrieve orderbook
    client.market.get_orderbook("005930")
    
    # Verify that the token call was made once
    assert len(responses.calls) == 2  # 1 for token, 1 for orderbook
    assert responses.calls[0].request.url == "https://openapi.tossinvest.com/oauth2/token"
    assert "grant_type=client_credentials" in responses.calls[0].request.body
    
    # Call again - token should be cached (no new token request)
    client.market.get_orderbook("005930")
    assert len(responses.calls) == 3  # only 1 more call (for orderbook)


@responses.activate
def test_token_auto_refresh_on_expiry(client):
    # Set up token expiring in 10 seconds (less than 60)
    mock_token_response(responses, expires_in=10)
    
    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/orderbook",
        json={"result": {"timestamp": "2026-03-25T09:30:00+09:00", "currency": "KRW", "asks": [], "bids": []}},
        status=200,
    )
    
    # First call: triggers token fetch
    client.market.get_orderbook("005930")
    
    # Token expires in 10s. Pre-request check should determine it is expiring and fetch a new one.
    client.market.get_orderbook("005930")
    
    # Should be 4 calls: token, orderbook, token, orderbook
    assert len(responses.calls) == 4
    assert responses.calls[0].request.url == "https://openapi.tossinvest.com/oauth2/token"
    assert responses.calls[2].request.url == "https://openapi.tossinvest.com/oauth2/token"


@responses.activate
def test_get_prices(client):
    mock_token_response(responses)
    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/prices",
        json={
            "result": [
                {
                    "symbol": "005930",
                    "timestamp": "2026-03-25T09:30:00.123+09:00",
                    "lastPrice": "72000",
                    "currency": "KRW",
                }
            ]
        },
        status=200,
    )
    
    prices = client.market.get_prices(["005930"])
    assert len(prices) == 1
    assert prices[0].symbol == "005930"
    assert prices[0].last_price == "72000"
    assert prices[0].currency == "KRW"
    
    # Check parameters
    assert "symbols=005930" in responses.calls[1].request.url


@responses.activate
def test_get_candles(client):
    mock_token_response(responses)
    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/candles",
        json={
            "result": {
                "candles": [
                    {
                        "timestamp": "2026-03-25T09:32:00+09:00",
                        "openPrice": "72000",
                        "highPrice": "72100",
                        "lowPrice": "71950",
                        "closePrice": "72050",
                        "volume": "15200",
                        "currency": "KRW",
                    }
                ],
                "nextBefore": "2026-03-25T09:31:00+09:00",
            }
        },
        status=200,
    )
    
    res = client.market.get_candles("005930", interval="1m", count=1, adjusted=True)
    assert len(res.candles) == 1
    assert res.candles[0].open_price == "72000"
    assert res.next_before == "2026-03-25T09:31:00+09:00"
    
    url = responses.calls[1].request.url
    assert "interval=1m" in url
    assert "count=1" in url
    assert "adjusted=true" in url


@responses.activate
def test_get_stock_info_and_warnings(client):
    mock_token_response(responses)
    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/stocks",
        json={
            "result": [
                {
                    "symbol": "AAPL",
                    "name": "애플",
                    "englishName": "APPLE INC",
                    "isinCode": "US0378331005",
                    "market": "NASDAQ",
                    "securityType": "STOCK",
                    "isCommonShare": True,
                    "status": "ACTIVE",
                    "currency": "USD",
                    "listDate": "1980-12-12",
                    "sharesOutstanding": "14702703000",
                    "leverageFactor": None,
                    "koreanMarketDetail": None,
                }
            ]
        },
        status=200,
    )
    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/stocks/AAPL/warnings",
        json={
            "result": [
                {
                    "warningType": "VI_STATIC",
                    "exchange": "NASDAQ",
                    "startDate": "2026-03-26",
                    "endDate": None,
                }
            ]
        },
        status=200,
    )
    
    stocks = client.stock.get_stocks(["AAPL"])
    assert len(stocks) == 1
    assert stocks[0].name == "애플"
    assert stocks[0].english_name == "APPLE INC"
    
    warnings = client.stock.get_warnings("AAPL")
    assert len(warnings) == 1
    assert warnings[0].warning_type == "VI_STATIC"


@responses.activate
def test_get_exchange_rate_and_calendars(client):
    mock_token_response(responses)
    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/exchange-rate",
        json={
            "result": {
                "baseCurrency": "USD",
                "quoteCurrency": "KRW",
                "rate": "1380.5",
                "midRate": "1375",
                "basisPoint": "40",
                "rateChangeType": "UP",
                "validFrom": "2026-03-25T09:30:00+09:00",
                "validUntil": "2026-03-25T09:31:00+09:00",
            }
        },
        status=200,
    )
    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/market-calendar/KR",
        json={
            "result": {
                "date": "2026-03-25",
                "isBusinessDay": True,
                "isMarketOpened": True,
                "marketOpenedDescription": "정규장",
            }
        },
        status=200,
    )
    
    rate = client.market_info.get_exchange_rate("USD", "KRW")
    assert rate.rate == "1380.5"
    
    cal = client.market_info.get_kr_calendar("2026-03-25")
    assert cal.is_business_day is True
    assert cal.market_opened_description == "정규장"


@responses.activate
def test_accounts_and_holdings(client):
    mock_token_response(responses)
    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/accounts",
        json={
            "result": [
                {
                    "accountNo": "12345678901",
                    "accountSeq": 42,
                    "accountType": "BROKERAGE",
                }
            ]
        },
        status=200,
    )
    
    # 1. Get Accounts
    accounts = client.account.get_accounts()
    assert len(accounts) == 1
    assert accounts[0].account_seq == 42
    
    # Try calling holding without setting account sequence -> raises TossInvestError
    with pytest.raises(TossInvestError) as exc_info:
        client.account.get_holdings()
    assert "This endpoint requires an account sequence" in str(exc_info.value)
    
    # Set default sequence
    client.account_seq = 42
    assert client.account_seq == 42
    
    # Mock holdings response
    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/holdings",
        json={
            "result": {
                "totalPurchaseAmount": {"amount": "1000000", "currency": "KRW"},
                "marketValue": {
                    "native": {"amount": "1200000", "currency": "KRW"},
                    "converted": {"amount": "1200000", "currency": "KRW"},
                },
                "profitLoss": {
                    "native": {"amount": "200000", "currency": "KRW"},
                    "converted": {"amount": "200000", "currency": "KRW"},
                },
                "dailyProfitLoss": {
                    "native": {"amount": "-5000", "currency": "KRW"},
                    "converted": {"amount": "-5000", "currency": "KRW"},
                },
                "items": [
                    {
                        "symbol": "005930",
                        "name": "삼성전자",
                        "marketCountry": "KR",
                        "currency": "KRW",
                        "quantity": "10",
                        "lastPrice": "72000",
                        "averagePurchasePrice": "65000",
                        "marketValue": {
                            "native": {"amount": "720000", "currency": "KRW"},
                            "converted": {"amount": "720000", "currency": "KRW"},
                        },
                        "profitLoss": {
                            "native": {"amount": "70000", "currency": "KRW"},
                            "converted": {"amount": "70000", "currency": "KRW"},
                        },
                        "dailyProfitLoss": {
                            "native": {"amount": "10000", "currency": "KRW"},
                            "converted": {"amount": "10000", "currency": "KRW"},
                        },
                        "cost": {
                            "native": {"amount": "650000", "currency": "KRW"},
                            "converted": {"amount": "650000", "currency": "KRW"},
                        },
                    }
                ],
            }
        },
        status=200,
    )
    
    holdings = client.account.get_holdings()
    assert holdings.total_purchase_amount.amount == "1000000"
    assert len(holdings.items) == 1
    assert holdings.items[0].name == "삼성전자"
    
    # Verify account header was passed
    last_req = responses.calls[-1].request
    assert last_req.headers["X-Tossinvest-Account"] == "42"


@responses.activate
def test_order_creation_and_history(client):
    mock_token_response(responses)
    client.account_seq = 42
    
    # 1. Mock order creation
    responses.add(
        responses.POST,
        "https://openapi.tossinvest.com/api/v1/orders",
        json={
            "result": {
                "orderId": "order_id_12345",
                "clientOrderId": "my-client-id",
            }
        },
        status=200,
    )
    
    # Quantity-based order
    res = client.order.create_order(
        symbol="005930",
        side="BUY",
        order_type="LIMIT",
        quantity="10",
        price="70000",
        client_order_id="my-client-id",
    )
    assert res.order_id == "order_id_12345"
    assert res.client_order_id == "my-client-id"
    
    # Amount-based order
    res_amt = client.order.create_amount_order(
        symbol="AAPL",
        side="BUY",
        order_amount="100.5",
    )
    assert res_amt.order_id == "order_id_12345"
    
    # Verify headers and bodies
    calls = [call.request for call in responses.calls if call.request.method == "POST"]
    assert calls[1].headers["X-Tossinvest-Account"] == "42"
    assert '"quantity": "10"' in calls[1].body
    assert '"price": "70000"' in calls[1].body
    assert '"orderAmount": "100.5"' in calls[2].body


@responses.activate
def test_order_modification_and_cancellation(client):
    mock_token_response(responses)
    client.account_seq = 42
    
    responses.add(
        responses.POST,
        "https://openapi.tossinvest.com/api/v1/orders/ord_123/modify",
        json={"result": {"orderId": "ord_123"}},
        status=200,
    )
    responses.add(
        responses.POST,
        "https://openapi.tossinvest.com/api/v1/orders/ord_123/cancel",
        json={"result": {"orderId": "ord_123"}},
        status=200,
    )
    
    res = client.order.modify_order("ord_123", order_type="LIMIT", price="71000", quantity="15")
    assert res.order_id == "ord_123"
    
    res_cancel = client.order.cancel_order("ord_123")
    assert res_cancel.order_id == "ord_123"


@responses.activate
def test_error_handling_toss_api(client):
    mock_token_response(responses)
    
    # Mock an error response (e.g. invalid order parameter)
    responses.add(
        responses.GET,
        "https://openapi.tossinvest.com/api/v1/prices",
        json={
            "error": {
                "requestId": "req_abc123",
                "code": "invalid-request",
                "message": "요청이 올바르지 않습니다.",
                "data": {
                    "field": "symbols",
                    "constraint": {"min": 1, "max": 200},
                },
            }
        },
        status=400,
    )
    
    with pytest.raises(TossInvestAPIError) as exc_info:
        client.market.get_prices(["005930"])
        
    err = exc_info.value
    assert err.status_code == 400
    assert err.request_id == "req_abc123"
    assert err.code == "invalid-request"
    assert err.message == "요청이 올바르지 않습니다."
    assert err.data == {"field": "symbols", "constraint": {"min": 1, "max": 200}}


@responses.activate
def test_error_handling_oauth(client):
    # Mock OAuth2 Client authentication failure
    responses.add(
        responses.POST,
        "https://openapi.tossinvest.com/oauth2/token",
        json={
            "error": "invalid_client",
            "error_description": "Client authentication failed.",
        },
        status=401,
    )
    
    with pytest.raises(TossInvestAuthError) as exc_info:
        client.market.get_prices(["005930"])
        
    err = exc_info.value
    assert err.status_code == 401
    assert err.error == "invalid_client"
    assert err.error_description == "Client authentication failed."
