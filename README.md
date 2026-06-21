# Toss Securities Open API Python Client

This package provides a clean, standard, and easy-to-use Python client for the Toss Securities Open API.

## Features

- **OAuth 2.0 Client Credentials**: Automated token issuance and background renewal 60 seconds prior to token expiration.
- **Market Data**: Bid/Ask Orderbook, Current Prices, Recent Trades, Price Limits, and OHLCV Candle Charts.
- **Stock Information**: Basic Reference data and Trading Warning flags (VI, liquidation, overheated).
- **Market Info**: KRW/USD Exchange Rates and KR/US Market Calendars.
- **Account & Assets**: Integrated portfolio asset holdings and balances.
- **Order Management**: Quantity-based (KR & US) and Amount-based (US fractional) stock trades, orders modification, cancelation, and live histories.
- **Structured Error Handling**: Rich domain exceptions representing exact API errors (`requestId`, `code`, `message`, `data`).

---

## Installation

Install the package locally in editable mode (or install from your own git repository):

```bash
# Clone the repository and install
git clone https://github.com/your-username/tossinvest-core.git
cd tossinvest-core
pip install .
```

To install with development dependencies (for running tests):
```bash
pip install -e ".[dev]"
```

---

## Quick Start

```python
from tossinvest import TossInvestClient, TossInvestAPIError

# 1. Initialize client
client = TossInvestClient(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    base_url="https://openapi.tossinvest.com"  # Optional, defaults to production
)

try:
    # 2. Get Current Prices (Public Market Data - Token auto-managed in background)
    prices = client.market.get_prices(["005930", "AAPL"])
    for price in prices:
        print(f"Ticker: {price.symbol} | Price: {price.last_price} {price.currency}")

    # 3. Retrieve Accounts (Requires Client Credentials Token)
    accounts = client.account.get_accounts()
    if not accounts:
        print("No active accounts found.")
    else:
        # 4. Set default account seq for subsequent account/order calls
        client.account_seq = accounts[0].account_seq
        print(f"Active Account: {accounts[0].account_no} (Seq: {client.account_seq})")

        # 5. Place a Quantity-Based Limit Buy Order
        order_res = client.order.create_order(
            symbol="005930",
            side="BUY",
            order_type="LIMIT",
            quantity="5",
            price="71000"
        )
        print(f"Limit Order placed. Order ID: {order_res.order_id}")

except TossInvestAPIError as e:
    print(f"API Error [{e.code}]: {e.message} (Request ID: {e.request_id})")
except Exception as e:
    print(f"General error: {e}")
```

---

## Detailed API Reference

The API endpoints are grouped under logical namespaces: `market`, `stock`, `market_info`, `account`, and `order`.

### 1. Market Data (`client.market`)

```python
# Bid/Ask Orderbook
orderbook = client.market.get_orderbook(symbol="005930")

# Batch Current Prices (up to 200 symbols)
prices = client.market.get_prices(symbols=["005930", "AAPL"])

# Recent Trades
trades = client.market.get_trades(symbol="005930", count=10)

# Daily Price Limits (Upper / Lower boundaries)
limits = client.market.get_price_limits(symbol="005930")

# OHLCV Candle Charts (e.g. 1-day candles, last 100 periods)
candles = client.market.get_candles(symbol="005930", interval="1d", count=100)
```

### 2. Stock Reference Info (`client.stock`)

```python
# Static stock reference data (market category, ISIN code, shares outstanding, etc.)
stocks = client.stock.get_stocks(symbols=["005930", "AAPL"])

# Active warnings / VI (Volatility Interruptions)
warnings = client.stock.get_warnings(symbol="005930")
```

### 3. Market Operations Info (`client.market_info`)

```python
# Exchange Rate
rate = client.market_info.get_exchange_rate(base_currency="USD", quote_currency="KRW")

# Market Calendar (KR & US)
kr_calendar = client.market_info.get_kr_calendar(date="2026-03-25")
us_calendar = client.market_info.get_us_calendar(date="2026-03-25")
```

### 4. Account & Holdings (`client.account`)

These endpoints require setting `client.account_seq = <account_seq>` beforehand.

```python
client.account_seq = 1  # Set default sequence

# Account holdings summary and list of items
holdings = client.account.get_holdings()

# Cash buying power for a specific currency
buying_power = client.account.get_buying_power(currency="KRW")

# Quantity of shares available to sell for a symbol
sellable = client.account.get_sellable_quantity(symbol="005930")

# Commissions detail for KR and US transactions
commissions = client.account.get_commissions()
```

### 5. Orders (`client.order`)

These endpoints require setting `client.account_seq = <account_seq>` beforehand.

```python
client.account_seq = 1

# Place quantity-based order (Shares quantity based)
order = client.order.create_order(
    symbol="005930",
    side="BUY",
    order_type="LIMIT",
    quantity="10",
    price="70000"
)

# Place amount-based order (USD amount based, US Market & Market order type only)
amt_order = client.order.create_amount_order(
    symbol="AAPL",
    side="BUY",
    order_amount="150.0"
)

# List pending/active orders
paginated_orders = client.order.get_orders(status="OPEN")

# Get detailed order status and executions
order_detail = client.order.get_order_detail(order_id=order.order_id)

# Modify order (Price / Quantity)
modified = client.order.modify_order(
    order_id=order.order_id,
    order_type="LIMIT",
    price="71000",
    quantity="12"
)

# Cancel order
canceled = client.order.cancel_order(order_id=order.order_id)
```

---

## Running Tests

Verify the client logic locally using `pytest`:

```bash
# Run all tests
python3 -m pytest -v
```
