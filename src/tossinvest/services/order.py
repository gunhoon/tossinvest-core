from typing import Any, Dict, Optional

from tossinvest.services.base import BaseService


class OrderService(BaseService):
    """Service to place, modify, cancel, and retrieve orders, and get trading-related info."""

    def create(
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

        return self.client._request(
            method="POST",
            path="/api/v1/orders",
            json=body,
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )

    def modify(
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

        return self.client._request(
            method="POST",
            path=f"/api/v1/orders/{order_id}/modify",
            json=body,
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )

    def cancel(
        self,
        order_id: str,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Cancel an existing pending order.

        Args:
            order_id: Order identifier to cancel.
            account_seq: Account identifier. Defaults to the client-level account_seq.
        """
        return self.client._request(
            method="POST",
            path=f"/api/v1/orders/{order_id}/cancel",
            json={},
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )

    def list(
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

        return self.client._request(
            method="GET",
            path="/api/v1/orders",
            params=params,
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )

    def get(
        self,
        order_id: str,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Retrieve detailed information for a specific order.

        Args:
            order_id: Order identifier.
            account_seq: Account identifier. Defaults to the client-level account_seq.
        """
        return self.client._request(
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
        return self.client._request(
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
        return self.client._request(
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
        return self.client._request(
            method="GET",
            path="/api/v1/commissions",
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )
