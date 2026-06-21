from typing import List, Optional

from tossinvest.models import (
    BuyingPowerResponse,
    Commission,
    Order,
    OrderResponse,
    PaginatedOrderResponse,
    SellableQuantityResponse,
)
from tossinvest.services.base import BaseService


class OrderService(BaseService):
    """주문 생성, 정정, 취소 및 목록/상세 조회, 매매 정보를 처리하는 서비스입니다."""

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
    ) -> OrderResponse:
        """주문 생성 (``POST /api/v1/orders``)

        매수 또는 매도 주문을 생성합니다.
        수량 지정 시 `quantity`(주 단위 수량) 또는 `orderAmount`(금액 단위 주문, 미국 정규장 전용) 중 하나를 정확히 지정해야 합니다.

        Args:
            symbol: 주문할 종목 심볼.
            side: 주문 구분 ('BUY' 또는 'SELL').
            order_type: 주문 유형 ('LIMIT' 지정가 또는 'MARKET' 시장가).
            quantity: 주문 수량 (주 단위).
            price: 주문 가격 (지정가 LIMIT 주문인 경우 필수).
            order_amount: 주문 금액 (달러 단위, 미국 주식 금액 주문인 경우 지정).
            time_in_force: 주문 효력 조건 ('DAY' 당일 유효 또는 'CLS' 종가).
            client_order_id: 멱등성 처리를 위한 클라이언트 고유 식별 번호.
            confirm_high_value_order: 1억 원 이상의 대량 주문 시 확인 여부 플래그.
            account_seq: 계좌 일련번호. 지정하지 않으면 클라이언트 기본값을 사용합니다.
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
    ) -> OrderResponse:
        """주문 정정 (``POST /api/v1/orders/{orderId}/modify``)

        기존 주문의 가격 또는 수량을 정정합니다.
        국내 주식은 수량(`quantity`) 지정이 필수적이나, 미국 주식은 가격 변경만 허용되며 수량 정정은 지원되지 않습니다.

        Args:
            order_id: 정정할 주문 ID.
            order_type: 주문 유형 ('LIMIT' 또는 'MARKET').
            quantity: 정정할 수량 (국내 주식 필수, 미국 주식은 지원하지 않음).
            price: 정정할 가격 (지정가 주문인 경우 필수).
            confirm_high_value_order: 1억 원 이상의 대량 주문 확인 여부 플래그.
            account_seq: 계좌 일련번호. 지정하지 않으면 클라이언트 기본값을 사용합니다.
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
    ) -> OrderResponse:
        """주문 취소 (``POST /api/v1/orders/{orderId}/cancel``)

        기존 주문을 취소합니다. 이미 체결된 주문은 취소할 수 없습니다.

        Args:
            order_id: 취소할 주문 ID.
            account_seq: 계좌 일련번호. 지정하지 않으면 클라이언트 기본값을 사용합니다.
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
    ) -> PaginatedOrderResponse:
        """주문 목록 조회 (``GET /api/v1/orders``)

        주문 목록을 조회합니다. status 파라미터로 주문 상태를 필터링합니다.

        Args:
            status: 주문 상태 그룹 필터 ('OPEN' 또는 'CLOSED').
            symbol: 특정 종목의 주문 내역만 필터링하기 위한 종목 심볼.
            from_date: 조회 시작일 (YYYY-MM-DD).
            to_date: 조회 종료일 (YYYY-MM-DD).
            cursor: 페이지네이션을 위한 커서 식별 번호 (CLOSED 주문 조회 시에만 적용).
            limit: 한 페이지에 반환할 최대 레코드 수 (CLOSED 주문 조회 시에만 적용, 기본값 20, 최대 100).
            account_seq: 계좌 일련번호. 지정하지 않으면 클라이언트 기본값을 사용합니다.
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
    ) -> Order:
        """주문 상세 조회 (``GET /api/v1/orders/{orderId}``)

        특정 주문의 상세 정보를 조회합니다. 모든 주문 상태(체결 완료, 취소, 거부 등)의 주문을 조회할 수 있습니다.

        Args:
            order_id: 조회할 주문 ID.
            account_seq: 계좌 일련번호. 지정하지 않으면 클라이언트 기본값을 사용합니다.
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
    ) -> BuyingPowerResponse:
        """매수 가능 금액 조회 (``GET /api/v1/buying-power``)

        매수 주문 시 사용할 수 있는 매수 가능 금액을 조회합니다. 미수거래를 제외한 현금 기반 매수 가능 금액(미수 미발생 기준)을 반환합니다.

        Args:
            currency: 통화 코드 ('KRW' 또는 'USD', 기본값 'KRW').
            account_seq: 계좌 일련번호. 지정하지 않으면 클라이언트 기본값을 사용합니다.
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
    ) -> SellableQuantityResponse:
        """판매 가능 수량 조회 (``GET /api/v1/sellable-quantity``)

        특정 종목의 판매 가능 수량을 조회합니다.

        Args:
            symbol: 대상 종목 심볼.
            account_seq: 계좌 일련번호. 지정하지 않으면 클라이언트 기본값을 사용합니다.
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
    ) -> List[Commission]:
        """매매 수수료 조회 (``GET /api/v1/commissions``)

        현재 계좌의 시장별 매매 수수료율을 조회합니다. 국내주식과 해외주식의 수수료 정보를 배열로 반환합니다.

        Args:
            account_seq: 계좌 일련번호. 지정하지 않으면 클라이언트 기본값을 사용합니다.
        """
        return self.client._request(
            method="GET",
            path="/api/v1/commissions",
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )
