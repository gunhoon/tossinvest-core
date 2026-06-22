from typing import List, Optional

from tossinvest.models import Account, HoldingsOverview
from tossinvest.services.base import BaseService


class AccountService(BaseService):
    """사용자 계좌 정보 및 보유 주식 자산을 조회하는 서비스입니다."""

    # --- Account & Asset APIs ---

    def get_accounts(self) -> List[Account]:
        """계좌 목록 조회 (``GET /api/v1/accounts``)

        사용자의 계좌 목록을 조회합니다. 현재는 종합매매(BROKERAGE) 계좌만 반환하며, 계좌가 없으면 빈 배열이 반환됩니다.
        """
        return self.client._request(
            method="GET",
            path="/api/v1/accounts",
            requires_auth=True,
            requires_account=False,
        )

    def get_holdings(
        self,
        account_seq: Optional[int] = None,
        symbol: Optional[str] = None,
    ) -> HoldingsOverview:
        """보유 주식 조회 (``GET /api/v1/holdings``)

        보유 주식 정보를 조회합니다. 국내(KR)·미국(US) 주식만 포함하며, 해외 옵션 및 채권은 제외합니다.
        보유 종목이 없으면 요약 금액은 0이고 items는 빈 배열이 반환됩니다.

        Args:
            account_seq: 계좌 일련번호 (X-Tossinvest-Account 헤더). 지정하지 않으면 클라이언트 기본값을 사용합니다.
            symbol: 특정 종목의 보유 정보를 필터링하기 위한 종목 심볼.
        """
        params = {}
        if symbol:
            params["symbol"] = symbol

        return self.client._request(
            method="GET",
            path="/api/v1/holdings",
            params=params,
            requires_auth=True,
            requires_account=True,
            account_seq=account_seq,
        )
