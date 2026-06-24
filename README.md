# 토스증권 Open API Python SDK (tossinvest-core)

토스증권 Open API를 파이썬 환경에서 쉽고 안전하게 연동할 수 있도록 돕는 서비스 지향 컴포지션 패턴(Service Composition Pattern) 기반의 Python SDK입니다. 

자동 토큰 만료 관리, 429 Rate Limit 자동 재시도, 다중 계좌 컨텍스트 지원, 세밀한 타입 힌팅 등 프로덕션 환경에 즉시 적용 가능한 완성도 높은 기능들을 제공합니다.

---

## 주요 특징

- **서비스 도메인 격리 (Service Composition)**: API 명세에 맞춰 시세(`market`), 계좌(`account`), 주문(`order`) 기능이 독립된 서비스 레이어로 설계되어 있어 자동완성과 가독성이 매우 뛰어납니다.
- **OAuth2 토큰 자동 수명 관리**: 인증 및 토큰 갱신 로직이 `TossInvestClient` 내부에서 자동으로 수행됩니다. 만료 60초 전 감지하여 자동으로 토큰을 재발급하므로 개발자가 수동으로 발급 상태를 걱정할 필요가 없습니다.
- **자동 429 재시도 (Retry-After 대응)**: API 호출 시 `429 Too Many Requests` 제한이 발생하면 헤더 및 응답 본문의 대기 시간을 자동으로 추출해 대기(sleep) 후 다시 시도합니다.
- **계좌 컨텍스트 제어**: 기본 계좌(`account_seq`)를 지정하여 번거로운 파라미터 지정을 생략할 수 있으며, 호출 시 특정 계좌 번호를 전달해 덮어쓰는 다중 계좌 환경도 완벽히 지원합니다.
- **명확한 예외 및 타입 힌트**: `TypedDict`와 `Enum`을 활용한 상세한 타입 정의([models.py](src/tossinvest/models.py)) 및 전용 커스텀 예외들을 제공하여 버그 예방과 디버깅을 돕습니다.

---

## 설치 방법

PyPI를 통한 간편 설치:

```bash
pip install tossinvest-core
```

로컬 소스 코드로 빌드 및 설치 시:

```bash
# 기본 설치
pip install .

# 개발용 모드 설치 (실시간 코드 수정 반영)
pip install -e .
```

---

## Quick Start

### 1. 클라이언트 초기화 및 인증

클라이언트 생성 시 토스증권에서 발급받은 `client_id`와 `client_secret`을 제공해야 합니다. 기본 계좌 번호(`account_seq`)와 429 발생 시 최대 재시도 횟수(`max_retries`)도 설정 가능합니다.

```python
import os
from tossinvest import TossInvestClient

# 토스증권 API 클라이언트 초기화
# 내부적으로 base_url("https://openapi.tossinvest.com")과 HTTP Session이 자동 생성 및 관리됩니다.
client = TossInvestClient(
    client_id=os.getenv("TOSS_CLIENT_ID", "your-client-id"),
    client_secret=os.getenv("TOSS_CLIENT_SECRET", "your-client-secret"),
    account_seq=1,       # API 요청 시 X-Tossinvest-Account 헤더로 전달될 기본 계좌 번호
    max_retries=3        # 429 Rate Limit 도달 시 자동 대기 후 재시도할 횟수
)

# 별도의 인증 함수 호출 없이, API 요청 시 내부에서 자동으로 OAuth2 토큰을 발급받아 캐싱 및 갱신합니다.
```

---

### 2. 시세 및 종목 정보 조회 (`market` 서비스)

국내/해외 주식의 현재가, 호가, 체결, 차트 정보, 환율 및 거래소 휴장일 일정을 조회할 수 있습니다.

```python
# A. 현재가 조회 (최대 200개 종목 다건 조회 가능)
prices = client.market.get_prices(["005930", "AAPL"])
for p in prices:
    print(f"종목: {p['symbol']}, 현재가: {p['lastPrice']} {p['currency']}")

# B. 호가 조회
orderbook = client.market.get_orderbook("005930")
print(f"매도1호가: {orderbook['ask'][0]['price']}, 매수1호가: {orderbook['bid'][0]['price']}")

# C. 최근 체결 내역 조회 (당일 최근 체결 내역을 최대 50개까지 조회)
trades = client.market.get_trades("005930", count=5)
for t in trades:
    print(f"시간: {t['timestamp']}, 체결가: {t['price']}, 체결량: {t['quantity']}")

# D. 당일 상한가 및 하한가 조회
limits = client.market.get_price_limits("005930")
print(f"상한가: {limits['upper']}, 하한가: {limits['lower']}")

# E. 캔들 차트 조회 (interval: '1m' 또는 '1d', 최대 200개 봉)
candles_res = client.market.get_candles("005930", interval="1d", count=10, adjusted=True)
for c in candles_res.get("candles", []):
    print(f"날짜: {c['timestamp']}, 시가: {c['openPrice']}, 종가: {c['closePrice']}")

# F. 종목 기본 정보 조회 (종목명, 시장구분, 결제통화, 상장상태, 거래정지 여부 등)
stocks_info = client.market.get_stocks(["005930", "AAPL"])
for s in stocks_info:
    print(f"종목명: {s['name']}, 시장: {s['market']}, 거래가능여부: {s['tradable']}")

# G. 매수 유의사항 및 VI 발동 정보 조회
warnings = client.market.get_stock_warnings("005930")
for w in warnings:
    print(f"유의타입: {w['type']}, 메시지: {w['message']}")

# H. 실시간 환율 조회 (기준통화 ↔ 상대통화)
exchange = client.market.get_exchange_rate(base_currency="USD", quote_currency="KRW")
print(f"기준환율: {exchange['basePrice']} (고시시간: {exchange['timestamp']})")

# I. 국내/해외 거래소 장 운영 정보 및 휴장일 조회 (country: 'KR' 또는 'US')
calendar = client.market.get_market_calendar(country="KR", date="2026-06-25")
print(f"영업여부: {calendar['businessDay']}, 장 구분: {calendar['status']}")
```

---

### 3. 계좌 및 자산 조회 (`account` 서비스)

등록된 계좌 목록과 각 계좌의 주식 보유 현황을 조회합니다.

```python
# A. 사용자 등록 계좌 목록 조회 (종합매매 계좌 등 정보 반환)
accounts = client.account.get_accounts()
for acc in accounts:
    print(f"계좌명: {acc['name']}, 계좌번호: {acc['accountNo']}, 순번: {acc['accountSeq']}")

# B. 보유 주식 현황 조회 (평가금액, 매입금액, 수익률, 각 종목별 평균매입가/보유수량 등)
# account_seq를 생략하면 초기화 시 설정한 기본값이 사용되며, 특정 계좌를 조회하려면 파라미터로 넘겨줍니다.
holdings = client.account.get_holdings(account_seq=1)
print(f"총 매입금액: {holdings['purchaseValue']['total']['krw']} KRW")
print(f"총 평가금액: {holdings['marketValue']['total']['krw']} KRW")
for item in holdings.get("items", []):
    print(f" - {item['name']}({item['symbol']}): {item['quantity']}주 (수익률: {item['profitRate']})")
```

---

### 4. 주식 주문 거래 (`order` 서비스)

주식의 신규 주문 제출, 정정 및 취소, 주문 상세/목록 조회, 매매 가능 수량/수수료 조회가 가능합니다.

```python
# A. 신규 주문 제출 (지정가 LIMIT 또는 시장가 MARKET)
# side: 'BUY' 또는 'SELL', quantity: 수량(주 단위), price: 지정가격(지정가 시 필수)
order_res = client.order.create_order(
    symbol="005930",
    side="BUY",
    order_type="LIMIT",
    quantity="10",
    price="60000",
    client_order_id="my-custom-uuid-001"  # 멱등성 보장을 위한 식별자 (선택)
)
order_id = order_res["orderId"]
print(f"매수 주문 완료: {order_id}")

# * 미국 주식의 경우 소수점 금액 주문(order_amount, 달러 단위)도 지원합니다.
# order_res = client.order.create_order(symbol="AAPL", side="BUY", order_type="MARKET", order_amount="100.50")

# B. 주문 정정
# 국내 주식은 가격과 수량 정정이 모두 가능하나, 미국 주식은 가격 정정만 가능합니다.
modified_res = client.order.modify_order(
    order_id=order_id,
    order_type="LIMIT",
    quantity="5",    # 정정할 수량
    price="60500"     # 정정할 가격
)
print(f"주문 정정 완료, 새 주문 ID: {modified_res['orderId']}")

# C. 주문 취소
cancelled_res = client.order.cancel_order(order_id=modified_res['orderId'])
print(f"주문 취소 접수완료: {cancelled_res['orderId']}")

# D. 주문 목록 조회 (status: 'OPEN' 미체결 또는 'CLOSED' 체결/취소완료)
orders_page = client.order.get_orders(status="CLOSED", symbol="005930", limit=10)
for ord in orders_page.get("orders", []):
    print(f"주문번호: {ord['orderId']}, 상태: {ord['status']}, 체결수량: {ord['filledQuantity']}")

# E. 단건 주문 상세 조회
order_detail = client.order.get_order_detail(order_id=order_id)
print(f"주문시간: {order_detail['orderedAt']}, 평균체결가: {order_detail['executionAveragePrice']}")

# F. 매수 가능 금액 조회 (currency: 'KRW' 또는 'USD')
buying_power = client.order.get_buying_power(currency="KRW")
print(f"현금 매수가능금액: {buying_power['buyingPower']} KRW")

# G. 판매 가능 수량 조회
sellable = client.order.get_sellable_quantity(symbol="005930")
print(f"매도 가능 잔량: {sellable['sellableQuantity']}주")

# H. 계좌별 시장별 수수료율 조회
commissions = client.order.get_commissions()
for comm in commissions:
    print(f"시장: {comm['market']}, 매수수수료: {comm['buyCommissionRate']}, 매도수수료: {comm['sellCommissionRate']}")
```

---

## 에러 핸들링

SDK는 예외 발생 시 예외의 종류에 따라 세분화된 커스텀 Exception 클래스를 발생시킵니다. 

- `TossInvestError`: SDK에서 발생하는 모든 오류의 기본 클래스입니다.
- `TossInvestAuthError`: OAuth2 토큰 발급에 실패한 경우 발생합니다.
- `TossInvestAPIError`: 토스증권 API가 에러 상태 코드를 응답한 경우 발생합니다.
  - `status_code`: HTTP 상태 코드
  - `code`: 토스증권 API 에러 코드 (예: `invalid-request`)
  - `message`: 에러 메시지
  - `data`: 에러 관련 힌트/상세 데이터 구조
  - `request_id`: 문제 추적을 위한 API Request ID (`X-Request-Id`)
- `TossInvestRateLimitError`: `429 Too Many Requests` 발생 후 최대 재시도(`max_retries`)에 도달했거나 재시도할 수 없을 때 발생합니다.
  - `retry_after_seconds`: API 서버가 지시한 대기 시간(초)

```python
from tossinvest import TossInvestClient
from tossinvest.exceptions import (
    TossInvestAuthError,
    TossInvestAPIError,
    TossInvestRateLimitError,
    TossInvestError
)

client = TossInvestClient(client_id="id", client_secret="secret")

try:
    prices = client.market.get_prices(["005930"])
except TossInvestAuthError as e:
    print(f"인증 오류 발생: {e}")
except TossInvestRateLimitError as e:
    print(f"API 호출 한도 초과 (대기필요시간: {e.retry_after_seconds}초): {e}")
except TossInvestAPIError as e:
    print(f"API 호출 실패 [{e.status_code}] (Request ID: {e.request_id})")
    print(f"코드: {e.code}, 메시지: {e.message}")
except TossInvestError as e:
    print(f"기타 SDK 내부 오류: {e}")
```

---

## 타입 힌트 및 모델

모든 API 응답 스키마는 `TypedDict`와 `Enum`을 기반으로 설계되었습니다. 이에 따라 개발자는 `pydantic` 같은 별도 유효성 검사 라이브러리 사용 부담 없이 정적 타입 검사(`mypy`, `pyright`)와 IDE 자동 완성 기능을 100% 누릴 수 있습니다.

```python
from tossinvest.models import PriceResponse, StockInfo, Order

# 타입 명시적 힌팅 활용 예시
def process_price(price: PriceResponse):
    symbol: str = price['symbol']
    last_price: str = price['lastPrice']
    # IDE에서 'symbol', 'lastPrice', 'currency' 등이 자동 완성됩니다.
```

---

## 라이선스

이 프로젝트는 MIT 라이선스에 따라 라이선스가 부여됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.
