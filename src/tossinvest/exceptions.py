class TossInvestError(Exception):
    """Base exception for Toss Securities Open API errors."""
    def __init__(
        self,
        message: str,
        code: str = None,
        request_id: str = None,
        data: dict = None,
        status_code: int = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.request_id = request_id
        self.data = data or {}
        self.status_code = status_code

    def __str__(self):
        parts = [f"[{self.status_code}]" if self.status_code else ""]
        if self.code:
            parts.append(f"code={self.code}")
        if self.request_id:
            parts.append(f"requestId={self.request_id}")
        parts.append(self.message)
        if self.data:
            parts.append(f"data={self.data}")
        return " ".join(filter(None, parts))


class BadRequestError(TossInvestError):
    """Raised on 400 Bad Request."""
    pass


class AuthenticationError(TossInvestError):
    """Raised on 401 Unauthorized."""
    pass


class ForbiddenError(TossInvestError):
    """Raised on 403 Forbidden."""
    pass


class NotFoundError(TossInvestError):
    """Raised on 404 Not Found."""
    pass


class ConflictError(TossInvestError):
    """Raised on 409 Conflict."""
    pass


class UnprocessableEntityError(TossInvestError):
    """Raised on 422 Unprocessable Entity."""
    pass


class RateLimitError(TossInvestError):
    """Raised on 429 Too Many Requests."""
    def __init__(
        self,
        message: str,
        code: str = None,
        request_id: str = None,
        data: dict = None,
        status_code: int = 429,
        retry_after: int = None,
    ):
        super().__init__(message, code, request_id, data, status_code)
        self.retry_after = retry_after

    def __str__(self):
        base_str = super().__str__()
        if self.retry_after is not None:
            return f"{base_str} (Retry-After: {self.retry_after}s)"
        return base_str


class ServerError(TossInvestError):
    """Raised on 500 Internal Server Error."""
    pass
