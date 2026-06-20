from typing import Dict, Any, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import TossInvestClient

class OrderService:
    """Handles order placement, modification, cancellation, history queries, and order info."""
    
    def __init__(self, client: "TossInvestClient"):
        self.client = client
        
    def create_order(
        self,
        order_req: Dict[str, Any],
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """주문 생성 (지정가·시장가 / KR·US).
        
        POST /api/v1/orders
        """
        return self.client.request(
            method="POST",
            path="/api/v1/orders",
            use_auth=True,
            require_account=True,
            account_seq=account_seq,
            json=order_req
        )
        
    def create_quantity_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Union[int, str],
        price: Optional[Union[float, int, str]] = None,
        time_in_force: str = "DAY",
        client_order_id: Optional[str] = None,
        confirm_high_value_order: bool = False,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """수량 기반 주문 생성 편리한 헬퍼 (KRX 및 미국 주식 공통).
        
        accepts int/float/str and formats them correctly for Toss API.
        """
        req_body: Dict[str, Any] = {
            "symbol": symbol,
            "side": side.upper(),
            "orderType": order_type.upper(),
            "quantity": str(quantity),
            "confirmHighValueOrder": confirm_high_value_order
        }
        
        if order_type.upper() == "LIMIT":
            if price is None:
                raise ValueError("price is required for LIMIT order")
            req_body["price"] = str(price)
            
        if time_in_force != "DAY":
            req_body["timeInForce"] = time_in_force
            
        if client_order_id:
            req_body["clientOrderId"] = client_order_id
            
        return self.create_order(req_body, account_seq=account_seq)
        
    def create_amount_order(
        self,
        symbol: str,
        side: str,
        order_amount: Union[float, int, str],
        client_order_id: Optional[str] = None,
        confirm_high_value_order: bool = False,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """금액 기반 주문 생성 편리한 헬퍼 (미국 주식 전용 소수점/금액 매매).
        
        accepts int/float/str and formats them correctly for Toss API.
        """
        req_body: Dict[str, Any] = {
            "symbol": symbol,
            "side": side.upper(),
            "orderType": "MARKET",
            "orderAmount": str(order_amount),
            "confirmHighValueOrder": confirm_high_value_order
        }
        
        if client_order_id:
            req_body["clientOrderId"] = client_order_id
            
        return self.create_order(req_body, account_seq=account_seq)
        
    def modify_order(
        self,
        order_id: str,
        order_type: str,
        price: Optional[Union[float, int, str]] = None,
        quantity: Optional[Union[int, str]] = None,
        confirm_high_value_order: bool = False,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """주문 정정 (가격·수량).
        
        POST /api/v1/orders/{orderId}/modify
        """
        req_body: Dict[str, Any] = {
            "orderType": order_type.upper(),
            "confirmHighValueOrder": confirm_high_value_order
        }
        
        if price is not None:
            req_body["price"] = str(price)
        if quantity is not None:
            req_body["quantity"] = str(quantity)
            
        return self.client.request(
            method="POST",
            path=f"/api/v1/orders/{order_id}/modify",
            use_auth=True,
            require_account=True,
            account_seq=account_seq,
            json=req_body
        )
        
    def cancel_order(
        self,
        order_id: str,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """주문 취소.
        
        POST /api/v1/orders/{orderId}/cancel
        """
        return self.client.request(
            method="POST",
            path=f"/api/v1/orders/{order_id}/cancel",
            use_auth=True,
            require_account=True,
            account_seq=account_seq,
            json={} # Schema expects an object, even if empty
        )
        
    def get_orders(
        self,
        status: str,
        symbol: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """주문 목록 조회 (대기중/종료).
        
        GET /api/v1/orders
        """
        params: Dict[str, Any] = {
            "status": status.upper() # OPEN or CLOSED
        }
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
            
        return self.client.request(
            method="GET",
            path="/api/v1/orders",
            use_auth=True,
            require_account=True,
            account_seq=account_seq,
            params=params
        )
        
    def get_order_detail(
        self,
        order_id: str,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """주문 상세 조회 (모든 상태).
        
        GET /api/v1/orders/{orderId}
        """
        return self.client.request(
            method="GET",
            path=f"/api/v1/orders/{order_id}",
            use_auth=True,
            require_account=True,
            account_seq=account_seq
        )
        
    def get_buying_power(
        self,
        currency: str = "KRW",
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """매수 가능 금액 조회 (현금 기반, KRW·USD).
        
        GET /api/v1/buying-power
        """
        return self.client.request(
            method="GET",
            path="/api/v1/buying-power",
            use_auth=True,
            require_account=True,
            account_seq=account_seq,
            params={"currency": currency}
        )
        
    def get_sellable_quantity(
        self,
        symbol: str,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """판매 가능 수량 조회.
        
        GET /api/v1/sellable-quantity
        """
        return self.client.request(
            method="GET",
            path="/api/v1/sellable-quantity",
            use_auth=True,
            require_account=True,
            account_seq=account_seq,
            params={"symbol": symbol}
        )
        
    def get_commissions(
        self,
        account_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """매매 수수료 조회 (KR·US 시장별).
        
        GET /api/v1/commissions
        """
        return self.client.request(
            method="GET",
            path="/api/v1/commissions",
            use_auth=True,
            require_account=True,
            account_seq=account_seq
        )
