from typing import Any, Dict, Optional


class TossInvestError(Exception):
    """Base exception class for all TossInvest errors."""
    pass


class TossInvestAuthError(TossInvestError):
    """Raised when authentication (token request) fails."""
    def __init__(self, message: str, response_body: Optional[str] = None) -> None:
        super().__init__(message)
        self.response_body = response_body


class TossInvestAPIError(TossInvestError):
    """Raised when an API request returns an error status code (4xx or 5xx)."""

    def __init__(
        self,
        request_id: Optional[str],
        code: str,
        message: str,
        data: Optional[Dict[str, Any]],
        status_code: int,
    ) -> None:
        super().__init__(f"[{status_code}] {code}: {message} (Request ID: {request_id})")
        self.request_id = request_id
        self.code = code
        self.message = message
        self.data = data or {}
        self.status_code = status_code


class TossInvestRateLimitError(TossInvestAPIError):
    """Raised when rate limits are exceeded (HTTP status 429)."""

    def __init__(
        self,
        request_id: Optional[str],
        code: str,
        message: str,
        data: Optional[Dict[str, Any]],
        status_code: int,
        retry_after_seconds: Optional[int] = None,
    ) -> None:
        super().__init__(request_id, code, message, data, status_code)
        self.retry_after_seconds = retry_after_seconds
