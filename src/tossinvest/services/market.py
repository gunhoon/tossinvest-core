from typing import List, Optional, Union

from tossinvest.models import (
    CandlePageResponse,
    ExchangeRateResponse,
    KrMarketCalendarResponse,
    OrderbookResponse,
    PriceLimitResponse,
    PriceResponse,
    StockInfo,
    StockWarning,
    Trade,
    UsMarketCalendarResponse,
)
from tossinvest.services.base import BaseService


class MarketService(BaseService):
    """시세 데이터, 종목 기본 정보, 환율 및 거래소 캘린더 정보를 제공하는 서비스입니다."""

    # --- Market Data APIs ---

    def get_orderbook(self, symbol: str) -> OrderbookResponse:
        """호가 조회 (``GET /api/v1/orderbook``)

        매수/매도 호가 및 잔량을 조회합니다.

        Args:
            symbol: 조회할 종목 심볼 (예: '005930' 또는 'AAPL').
        """
        return self.client._request(
            method="GET",
            path="/api/v1/orderbook",
            params={"symbol": symbol},
        )

    def get_prices(self, symbols: List[str]) -> List[PriceResponse]:
        """현재가 조회 (``GET /api/v1/prices``)

        종목의 현재가 정보를 조회합니다. 최대 200건 까지 다건 조회를 지원하며 콤마(`,`)로 구분합니다.

        Args:
            symbols: 조회할 종목 심볼 리스트 (예: ['005930', 'AAPL']).
        """
        if not symbols:
            raise ValueError("symbols list cannot be empty.")
        symbols_str = ",".join(symbols)
        return self.client._request(
            method="GET",
            path="/api/v1/prices",
            params={"symbols": symbols_str},
        )

    def get_trades(self, symbol: str, count: Optional[int] = None) -> List[Trade]:
        """최근 체결 내역 조회 (``GET /api/v1/trades``)

        당일 최근 체결 내역을 조회합니다.

        Args:
            symbol: 조회할 종목 심볼.
            count: 조회할 체결 내역 개수 (최대 50개).
        """
        params = {"symbol": symbol}
        if count is not None:
            params["count"] = count
        return self.client._request(
            method="GET",
            path="/api/v1/trades",
            params=params,
        )

    def get_price_limits(self, symbol: str) -> PriceLimitResponse:
        """상/하한가 조회 (``GET /api/v1/price-limits``)

        종목의 당일 상한가 및 하한가를 조회합니다.

        Args:
            symbol: 조회할 종목 심볼.
        """
        return self.client._request(
            method="GET",
            path="/api/v1/price-limits",
            params={"symbol": symbol},
        )

    def get_candles(
        self,
        symbol: str,
        interval: str,
        count: Optional[int] = None,
        before: Optional[str] = None,
        adjusted: Optional[bool] = None,
    ) -> CandlePageResponse:
        """캔들 차트 조회 (``GET /api/v1/candles``)

        종목의 캔들(OHLCV) 차트 데이터를 조회합니다. 최대 200개 봉을 반환합니다.

        Args:
            symbol: 조회할 종목 심볼.
            interval: 봉 단위 ('1m' 또는 '1d').
            count: 조회할 캔들 개수 (최대 200개).
            before: 페이지네이션 기준 시점 (미포함, ISO 8601 문자열).
            adjusted: 수정주가 적용 여부 (기본값: True).
        """
        params = {"symbol": symbol, "interval": interval}
        if count is not None:
            params["count"] = count
        if before is not None:
            params["before"] = before
        if adjusted is not None:
            params["adjusted"] = "true" if adjusted else "false"

        return self.client._request(
            method="GET",
            path="/api/v1/candles",
            params=params,
        )

    # --- Stock Info APIs ---

    def get_stocks(self, symbols: List[str]) -> List[StockInfo]:
        """종목 기본 정보 조회 (``GET /api/v1/stocks``)

        종목의 기본 정보를 조회합니다. `symbols` 를 콤마로 구분하여 최대 200건 까지 다건 조회를 지원합니다.
        종목명, 시장, 통화, 상장 상태, 거래정지 여부 등 트레이딩에서 필요한 참조 데이터를 제공합니다.

        Args:
            symbols: 조회할 종목 심볼 리스트 (예: ['005930', 'AAPL']).
        """
        if not symbols:
            raise ValueError("symbols list cannot be empty.")
        symbols_str = ",".join(symbols)
        return self.client._request(
            method="GET",
            path="/api/v1/stocks",
            params={"symbols": symbols_str},
        )

    def get_stock_warnings(self, symbol: str) -> List[StockWarning]:
        """매수 유의사항 조회 (``GET /api/v1/stocks/{symbol}/warnings``)

        종목의 매수 유의사항 및 변동성 완화(VI) 발동 정보를 조회합니다.

        Args:
            symbol: 조회할 종목 심볼.
        """
        return self.client._request(
            method="GET",
            path=f"/api/v1/stocks/{symbol}/warnings",
        )

    # --- Market Info APIs ---

    def get_exchange_rate(
        self,
        base_currency: str = "USD",
        quote_currency: str = "KRW",
        date_time: Optional[str] = None,
    ) -> ExchangeRateResponse:
        """환율 조회 (``GET /api/v1/exchange-rate``)

        KRW ↔ USD 환율 정보를 조회합니다.

        갱신 주기는 1분이며, 참고용 표시 환율입니다. 실제 주문 시 적용되는 거래 환율과 다를 수 있습니다.

        Args:
            base_currency: 기준 통화 (기본값: 'USD').
            quote_currency: 상대 통화 (기본값: 'KRW').
            date_time: 특정 시점의 환율 조회를 위한 ISO 8601 타임스탬프 (미지정 시 현재 유효 환율 조회).
        """
        params = {
            "baseCurrency": base_currency,
            "quoteCurrency": quote_currency,
        }
        if date_time:
            params["dateTime"] = date_time
        return self.client._request(
            method="GET",
            path="/api/v1/exchange-rate",
            params=params,
        )

    def get_market_calendar(
        self, country: str, date: Optional[str] = None
    ) -> Union[KrMarketCalendarResponse, UsMarketCalendarResponse]:
        """국내/해외 장 운영 정보 조회 (``GET /api/v1/market-calendar/{country}``)

        국내(KR) 또는 해외(US) 시장의 거래 가능 시간 및 장 운영 시간을 조회합니다.

        Args:
            country: 국가 코드 ('KR' 또는 'US').
            date: 기준 일자 (YYYY-MM-DD).
        """
        country_upper = country.upper()
        if country_upper not in ("KR", "US"):
            raise ValueError("country must be 'KR' or 'US'.")

        params = {}
        if date:
            params["date"] = date

        return self.client._request(
            method="GET",
            path=f"/api/v1/market-calendar/{country_upper}",
            params=params,
        )
