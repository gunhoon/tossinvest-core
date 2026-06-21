from typing import Optional

from tossinvest.base import APIGroup
from tossinvest.models import (
    from_dict,
    Order,
    OrderResponse,
    PaginatedOrderResponse,
)


class OrderAPI(APIGroup):
    """Order operations (create, list, cancel, modify, detail)."""

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: Optional[str] = None,
        time_in_force: str = "DAY",
        client_order_id: Optional[str] = None,
        confirm_high_value_order: bool = False,
    ) -> OrderResponse:
        """Create a quantity-based stock buy/sell order."""
        payload = {
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "timeInForce": time_in_force,
            "quantity": quantity,
            "confirmHighValueOrder": confirm_high_value_order,
        }
        if price is not None:
            payload["price"] = price
        if client_order_id is not None:
            payload["clientOrderId"] = client_order_id

        data = self._client._request("POST", "/api/v1/orders", json=payload, account_required=True)
        return from_dict(OrderResponse, data)

    def create_amount_order(
        self,
        symbol: str,
        side: str,
        order_amount: str,
        client_order_id: Optional[str] = None,
        confirm_high_value_order: bool = False,
    ) -> OrderResponse:
        """Create an amount-based stock buy/sell order (US MARKET ONLY, MARKET type only)."""
        payload = {
            "symbol": symbol,
            "side": side,
            "orderType": "MARKET",
            "orderAmount": order_amount,
            "confirmHighValueOrder": confirm_high_value_order,
        }
        if client_order_id is not None:
            payload["clientOrderId"] = client_order_id

        data = self._client._request("POST", "/api/v1/orders", json=payload, account_required=True)
        return from_dict(OrderResponse, data)

    def get_orders(
        self,
        status: str,
        symbol: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> PaginatedOrderResponse:
        """List orders. Requires X-Tossinvest-Account header."""
        params = {"status": status}
        if symbol is not None:
            params["symbol"] = symbol
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit

        data = self._client._request("GET", "/api/v1/orders", params=params, account_required=True)
        return from_dict(PaginatedOrderResponse, data)

    def get_order_detail(self, order_id: str) -> Order:
        """Get order detail by order ID. Requires X-Tossinvest-Account header."""
        data = self._client._request("GET", f"/api/v1/orders/{order_id}", account_required=True)
        return from_dict(Order, data)

    def modify_order(
        self,
        order_id: str,
        order_type: str,
        price: Optional[str] = None,
        quantity: Optional[str] = None,
        confirm_high_value_order: bool = False,
    ) -> OrderResponse:
        """Modify a pending order. Requires X-Tossinvest-Account header."""
        payload = {
            "orderType": order_type,
            "confirmHighValueOrder": confirm_high_value_order,
        }
        if price is not None:
            payload["price"] = price
        if quantity is not None:
            payload["quantity"] = quantity

        data = self._client._request(
            "POST",
            f"/api/v1/orders/{order_id}/modify",
            json=payload,
            account_required=True,
        )
        return from_dict(OrderResponse, data)

    def cancel_order(
        self,
        order_id: str,
        client_order_id: Optional[str] = None,
    ) -> OrderResponse:
        """Cancel a pending order. Requires X-Tossinvest-Account header."""
        payload = {}
        if client_order_id is not None:
            payload["clientOrderId"] = client_order_id
        data = self._client._request(
            "POST",
            f"/api/v1/orders/{order_id}/cancel",
            json=payload,
            account_required=True,
        )
        return from_dict(OrderResponse, data)
