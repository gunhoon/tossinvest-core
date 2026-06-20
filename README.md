# 토스증권 Open API Python SDK (`tossinvest-core`)

이 패키지는 토스증권(Toss Securities) Open API를 편리하게 호출할 수 있도록 돕는 Python SDK입니다. 가장 대중적이고 유지보수가 용이한 디자인 패턴을 적용하여 구현되었습니다.

## 주요 기능

1. **OAuth 2.0 자동 인증 처리**: 최초 API 호출 시 또는 토큰 만료(401) 시 자동으로 토큰 발급 및 재요청(Auto-Retry)을 수행합니다.
2. **속도 제한(Rate Limit) 대응**: API 초당 호출 한도 초과(429) 시 `Retry-After` 헤더 값을 파싱하여 지연 후 재요청(Auto-Backoff)합니다.
3. **직관적인 서비스 구조**: 도메인(Auth, Market, Account, Order) 별로 Namespace가 나뉘어 있어 API를 가독성 높게 사용 가능합니다.
4. **편리한 주문 헬퍼**: 수량 기반 주문(`create_quantity_order`) 및 미국 주식 소수점/금액 기반 주문(`create_amount_order`)을 제공하며, API가 요구하는 문자열(String) 포맷 변환을 자동 처리합니다.
5. **명시적 에러 처리**: 토스증권 Open API 에러 코드를 Python의 커스텀 예외 클래스(e.g., `AuthenticationError`, `RateLimitExceeded`, `InvalidRequestError` 등)로 매핑합니다.

---

## 설치 방법

현재 패키지는 소스 코드로 제공됩니다. 프로젝트 루트 디렉토리에서 다음과 같이 의존성을 설치하고 패키지를 사용할 수 있습니다.

```bash
pip install -r requirements.txt
# 또는 패키지 형태로 빌드/설치
pip install -e .
```

> **의존성 패키지**: `requests` (>=2.28.0)가 요구됩니다.

---

## 빠른 시작 (Quick Start)

### 1. 클라이언트 초기화 및 인증

설정 > Open API에서 발급받은 `client_id`와 `client_secret`을 사용해 클라이언트를 초기화합니다.

```python
from tossinvest import TossInvestClient

# 클라이언트 초기화
client = TossInvestClient(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    # 기본값은 실서버 주소인 https://openapi.tossinvest.com 입니다.
    base_url="https://openapi.tossinvest.com",
    # 계좌 관련 API에서 기본으로 사용할 계좌 식별 키(accountSeq)를 설정할 수 있습니다.
    account_seq=1 
)
```

---

### 2. 시세 및 종목 정보 조회 (인증 토큰만 필요)

시세, 캘린더, 환율 조회 등은 계좌 정보 없이 토큰 정보만으로 조회 가능합니다.

```python
# 1. 현재가 조회 (여러 종목을 리스트 혹은 콤마 구분자 문자열로 전달 가능)
prices = client.market.get_prices(["005930", "000660"])
print(prices)

# 2. 호가 조회
orderbook = client.market.get_orderbook("005930")
print(orderbook)

# 3. 캔들 차트 조회 (1분봉: "1m", 일봉: "1d")
candles = client.market.get_candles(symbol="005930", interval="1d", count=10)
print(candles)

# 4. KRW/USD 환율 조회
exchange_rate = client.market.get_exchange_rate(base_currency="USD", quote_currency="KRW")
print(exchange_rate)
```

---

### 3. 계좌 및 자산 조회 (계좌 번호 필요)

보유 자산 및 주문 관련 API를 호출할 때는 `account_seq` 헤더가 필수적입니다. 클라이언트 생성 시 전달한 계좌번호(`account_seq`)가 기본으로 적용되며, 필요한 경우 개별 메서드에서 임의로 오버라이드할 수 있습니다.

```python
# 1. 연결된 전체 계좌 목록 조회 (이 API는 accountSeq 헤더가 불필요합니다)
accounts = client.account.get_accounts()
print(accounts)

# 2. 특정 계좌의 보유 자산 조회
holdings = client.account.get_holdings()  # client.account_seq 계좌 사용
# 또는 특정 계좌 직접 지정: client.account.get_holdings(account_seq=2)
print(holdings)
```

---

### 4. 주식 주문 거래 (주문 및 잔고 확인)

#### 4-1. 수량 기반 주문 (국내 및 해외 주식 공통)

```python
# 삼성전자 10주를 70,000원에 지정가 매수 주문
order = client.order.create_quantity_order(
    symbol="005930",
    side="BUY",
    order_type="LIMIT",
    quantity=10,
    price=70000,
    confirm_high_value_order=False  # 1억원 이상 주문 시 True 설정 필수
)
print(f"주문이 접수되었습니다. 주문 ID: {order['orderId']}")
```

#### 4-2. 금액 기반 주문 (미국 주식 전용 / 소수점 매매)

```python
# 애플(AAPL) 주식을 $100.5 만큼 시장가 매수 주문
order = client.order.create_amount_order(
    symbol="AAPL",
    side="BUY",
    order_amount=100.5
)
print(f"주문이 접수되었습니다. 주문 ID: {order['orderId']}")
```

#### 4-3. 주문 정정, 취소 및 상세 조회

```python
# 주문 정정 (가격 71,000원, 수량 15주로 정정)
modified = client.order.modify_order(
    order_id="YOUR_ORDER_ID",
    order_type="LIMIT",
    price=71000,
    quantity=15
)

# 주문 취소
canceled = client.order.cancel_order(order_id="YOUR_ORDER_ID")

# 주문 목록 및 세부 사항 조회
open_orders = client.order.get_orders(status="OPEN")
order_detail = client.order.get_order_detail(order_id="YOUR_ORDER_ID")
```

#### 4-4. 계좌 거래 가능 정보 조회

```python
# 매수 가능 원화 예수금 조회
buying_power = client.order.get_buying_power(currency="KRW")

# 특정 종목 판매 가능 수량 조회
sellable = client.order.get_sellable_quantity(symbol="005930")
```

---

## 예외 처리 (Exception Handling)

네트워크 문제 또는 토스증권 API 서버에서 리턴한 에러 코드는 상황에 맞는 구체적인 예외 객체로 반환됩니다.

```python
from tossinvest import (
    TossInvestAPIError,
    InvalidRequestError,
    AuthenticationError,
    RateLimitExceeded,
    UnprocessableEntityError
)

try:
    client.order.create_quantity_order("005930", "BUY", "LIMIT", 10, 70000)
except InvalidRequestError as e:
    # 400 Bad Request: 호가 유효 범위 오류 등
    print(f"잘못된 요청: {e.message} (코드: {e.code}, Request ID: {e.request_id})")
except UnprocessableEntityError as e:
    # 422 Unprocessable Entity: 예수금 부족, 거래 제한 종목 등
    print(f"거래 제한 오류: {e.message}")
except RateLimitExceeded as e:
    # 429 Too Many Requests: 초당 호출 한도 초과 및 재시도 최대 횟수 도달
    print(f"호출 한도 초과: {e.message}")
except TossInvestAPIError as e:
    # 기타 API 반환 에러
    print(f"API 에러: {e}")
```

---

## 고급 설정

### 속도 제한(Rate Limit) 대응 비활성화
만약 초당 한도 초과(429) 시 클라이언트가 대기하지 않고 즉시 예외를 발생시키도록 설정하려면 다음과 같이 `auto_retry_rate_limit`을 `False`로 초기화합니다.

```python
client = TossInvestClient(
    client_id="xxx",
    client_secret="yyy",
    auto_retry_rate_limit=False
)
```

---

## 테스트 실행 (Testing)

이 패키지는 `pytest`를 사용하여 테스트가 작성되었습니다. 다음과 같이 테스트를 실행할 수 있습니다.

```bash
# pytest 설치 (필요시)
pip install pytest

# 테스트 실행
PYTHONPATH=src pytest
```

