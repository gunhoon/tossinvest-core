# tossinvest-core

토스증권 Open API를 파이썬 환경에서 쉽고 안전하게 연동할 수 있도록 돕는 서비스 지향 컴포지션 패턴(Service Composition Pattern) 기반의 Python SDK입니다.

---

## 주요 특징

- **서비스 분리 설계 (Service composition)**: 토스증권 Open API 명세에 따라 인증, 시세, 계좌, 주문 기능을 독립된 서비스 레이어(`auth`, `market`, `account`, `order`)로 격리하여 코드의 가독성 및 유지보수성을 극대화하였습니다.
- **자동 토큰 갱신**: OAuth2 Access Token의 만료 시간(Expires in)을 감지하고 만료 60초 전에 자동으로 토큰을 발급/갱신하므로 개발자가 수동으로 인증 상태를 관리할 필요가 없습니다.
- **계좌 컨텍스트 관리**: 클라이언트 수준에서 기본 `account_seq`(`X-Tossinvest-Account` 헤더)를 지정할 수 있고, 개별 API 호출 시점에 특정 계좌로 덮어쓰거나 변경하여 다중 계좌 환경을 유연하게 대처할 수 있습니다.
- **타입 힌트 및 자동완성**: Python `TypedDict` 및 `Enum`을 활용한 상세한 타입 선언([models.py](src/tossinvest/models.py))으로 IDE의 자동완성 혜택과 정적 분석 검증을 극대화하였습니다.
- **구조화된 예외 처리**: 서버 응답 결과 및 예외 원인(`requestId`, `code`, `message`, `data` 힌트)을 파싱하여 구체적인 커스텀 예외(`TossInvestAPIError`, `TossInvestRateLimitError` 등)로 래핑하여 제공합니다.

---

## 디렉토리 구조

```
tossinvest-core/
├── pyproject.toml      # 패키지 빌드 명세 및 requests 의존성 정의
├── src/
│   └── tossinvest/
│       ├── __init__.py # 패키지 진입점 (익스포트 정의)
│       ├── client.py   # HTTP 세션 관리 및 Transporter 역할의 메인 클라이언트
│       ├── exceptions.py # 커스텀 예외군 정의
│       ├── models.py   # 타입힌팅 스키마 (TypedDict & Enum)
│       └── services/   # 비즈니스 서비스 도메인
│           ├── __init__.py
│           ├── base.py # 메인 클라이언트를 참조하는 공통 BaseService
│           ├── auth.py # 토큰 생명주기 및 /oauth2/token 연동
│           ├── market.py # 시세, 종목 상세, 환율 및 캘린더 연동
│           ├── account.py # 계좌 목록 및 보유 자산 조회
│           └── order.py # 주문 생성/정정/취소 및 매수/매도 가능 정보 조회
└── tests/
    └── test_client.py  # pytest 기반 유닛 테스트 스위트
```

---

## 설치 방법

### 로컬 소스코드 설치
패키지 디렉토리 내부에서 pip를 이용하여 설치를 진행합니다.

```bash
pip install .
```

개발용 모드로 설치하려면 `-e` 옵션을 이용해 설치합니다.
```bash
pip install -e .
```

---

## Quick Start

```python
import os
from tossinvest import TossInvestClient, TossInvestAPIError

# 1. 클라이언트 초기화
# TOSS_CLIENT_ID 및 TOSS_CLIENT_SECRET 환경 변수가 필요합니다.
client = TossInvestClient(
    client_id=os.getenv("TOSS_CLIENT_ID", "your-client-id"),
    client_secret=os.getenv("TOSS_CLIENT_SECRET", "your-client-secret"),
    account_seq=1  # 기본 계좌 식별 번호 설정 (X-Tossinvest-Account 헤더로 사용됨)
)

try:
    # 2. 국내/해외 주식 시세 조회 (MarketService)
    prices = client.market.get_prices(["005930", "AAPL"])
    for p in prices:
        print(f"종목: {p['symbol']}, 현재가: {p['lastPrice']} {p['currency']}")

    # 3. 등록된 계좌 목록 조회 (AccountService)
    accounts = client.account.get_accounts()
    for acc in accounts:
        print(f"계좌명: {acc['name']}, 계좌번호: {acc['accountNo']}, 순번: {acc['accountSeq']}")

    # 4. 주식 주문 제출 (OrderService)
    # 삼성전자(005930) 60,000원에 1주 지정가(LIMIT) 매수 주문 제출
    order_res = client.order.create(
        symbol="005930",
        side="BUY",
        order_type="LIMIT",
        quantity="1",
        price="60000",
        client_order_id="my-custom-order-001"
    )
    order_id = order_res["orderId"]
    print(f"주문이 완료되었습니다. 주문ID: {order_id}")

    # 5. 주문 취소 (OrderService)
    client.order.cancel(order_id=order_id)
    print("주문이 성공적으로 취소되었습니다.")

except TossInvestAPIError as e:
    # API 호출 실패 시 상세 에러 처리
    print(f"API 에러 발생 [{e.status_code}]: Code={e.code}, Message={e.message}")
    if e.data:
        print(f"상세 힌트: {e.data}")
except Exception as e:
    print(f"일반 에러: {e}")
```

더 다양한 활용 방법은 [examples/demo.py](examples/demo.py) 예제 스크립트를 참조해 주세요.

---

## 개발자 가이드 (테스트 실행)

`tossinvest-core` 개발을 위해 가상환경(venv)을 구성하고 테스트를 진행하는 방법은 다음과 같습니다.

### 테스트 의존성 설치
단위 테스트 작성을 위해 `pytest` 및 관련 패키지가 필요합니다.

```bash
pip install pytest
```

### 테스트 실행
패키지 루트 디렉토리에서 `pytest`를 실행합니다.

```bash
pytest
```

또는 내장 `unittest` 모듈을 이용하여 테스트를 탐색 및 실행할 수 있습니다.

```bash
python3 -m unittest discover -s tests
```
