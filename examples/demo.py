import os
import sys

# Ensure src/ is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from tossinvest import (
    TossInvestAPIError,
    TossInvestAuthError,
    TossInvestClient,
    TossInvestError,
    TossInvestRateLimitError,
)


def run_demo():
    # 1. Initialize client using client credentials
    client_id = os.getenv("TOSS_CLIENT_ID", "your-client-id")
    client_secret = os.getenv("TOSS_CLIENT_SECRET", "your-client-secret")
    
    print("=== 1. Initializing TossInvestClient ===")
    # Optionally specify a default account_seq (e.g. 1) if known,
    # or pass it to individual service methods.
    client = TossInvestClient(
        client_id=client_id,
        client_secret=client_secret,
        account_seq=1,  # Set default account sequence header
    )
    print("Client initialized successfully.")

    try:
        # 1.5 Manually fetch token if needed (optional, as client handles this automatically)
        # token_info = client.issue_token()
        # print(f"Manual token fetch: {token_info['access_token'][:10]}...")

        # 2. Get current stock prices via MarketService
        print("\n=== 2. Fetching Stock Prices ===")
        symbols = ["005930", "AAPL"]  # Samsung Electronics (KRX), Apple (NASDAQ)
        prices = client.market.get_prices(symbols)
        print(f"Prices for {symbols}:")
        for p in prices:
            print(f"  - Symbol: {p.get('symbol')}, Current Price: {p.get('lastPrice')} {p.get('currency')}")

        # 3. Get candles via MarketService
        print("\n=== 3. Fetching Candles (1-day interval) ===")
        candles_res = client.market.get_candles(symbol="005930", interval="1d", count=5)
        candles = candles_res.get("candles", [])
        print(f"Last 5 daily candles for Samsung Electronics:")
        for c in candles:
            print(f"  - Time: {c.get('timestamp')}, Close: {c.get('closePrice')}, Volume: {c.get('volume')}")

        # 4. Get registered accounts via AccountService
        print("\n=== 4. Fetching Registered Accounts ===")
        accounts = client.account.get_accounts()
        print("Registered Accounts:")
        for acc in accounts:
            print(f"  - Seq: {acc.get('accountSeq')}, Name: {acc.get('name')}, Type: {acc.get('type')}")

        # 5. Fetch account holdings via AccountService
        print("\n=== 5. Fetching Account Holdings ===")
        holdings = client.account.get_holdings()  # Uses client-level default account_seq
        print("Holdings Summary:")
        total_value = holdings.get("marketValue", {}).get("total", {})
        print(f"  - Total Portfolio Value: KRW {total_value.get('krw')}, USD {total_value.get('usd')}")
        print("Holding items:")
        for item in holdings.get("items", []):
            print(f"  - Stock: {item.get('name')} ({item.get('symbol')}), Quantity: {item.get('quantity')}, Average Cost: {item.get('averagePurchasePrice')}")

        # 6. Buying Power (Available Cash) via OrderService
        print("\n=== 6. Fetching Buying Power ===")
        buying_power = client.order.get_buying_power(currency="KRW")
        print(f"Buying Power: KRW {buying_power.get('buyingPower')}")

        # 7. Create, modify, and cancel an order via OrderService
        print("\n=== 7. Order Management Flow ===")
        # Creating a quantity-based limit buy order for Samsung Electronics at 60,000 KRW
        print("Placing buy order for Samsung Electronics...")
        order = client.order.create_order(
            symbol="005930",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            price="60000",
            client_order_id="my-unique-order-001",
        )
        order_id = order.get("orderId")
        print(f"Order placed successfully! Order ID: {order_id}")

        # Modify order price to 59,500 KRW
        print(f"Modifying order {order_id}...")
        mod_order = client.order.modify_order(
            order_id=order_id,
            order_type="LIMIT",
            price="59500",
            quantity="1",
        )
        print(f"Order modified! New Order ID: {mod_order.get('orderId')}")

        # Cancel the modified order
        print(f"Canceling order {mod_order.get('orderId')}...")
        cancel_res = client.order.cancel_order(order_id=mod_order.get("orderId"))
        print(f"Order canceled! ID returned: {cancel_res.get('orderId')}")

    except TossInvestAuthError as e:
        print(f"\n[AuthError] Authentication failed.")
        print(f"Message: {e}")
        print(f"Raw Response: {e.response_body}")
    except TossInvestRateLimitError as e:
        print(f"\n[RateLimitError] Exceeded API rate limits.")
        print(f"Code: {e.code}, Message: {e.message}")
        print(f"Retry recommended after: {e.retry_after_seconds} seconds")
    except TossInvestAPIError as e:
        print(f"\n[APIError] API returned failure status code {e.status_code}")
        print(f"Code: {e.code}, Message: {e.message}")
        if e.data:
            print(f"Error data hints: {e.data}")
    except TossInvestError as e:
        print(f"\n[Error] SDK Error occurred: {e}")


if __name__ == "__main__":
    run_demo()
