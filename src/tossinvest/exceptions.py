class TossInvestError(Exception):
    """Base exception for all Toss Securities Open API errors."""
    pass


class TossInvestAuthError(TossInvestError):
    """Exception raised when authentication fails (OAuth2 token endpoint errors)."""

    def __init__(self, error: str, error_description: str = "", status_code: int = 400):
        self.error = error
        self.error_description = error_description
        self.status_code = status_code
        message = f"Auth failed ({status_code}): {error}"
        if error_description:
            message += f" - {error_description}"
        super().__init__(message)


class TossInvestAPIError(TossInvestError):
    """Exception raised when the Toss Securities API returns an error response (4xx/5xx)."""

    def __init__(
        self,
        status_code: int,
        request_id: str,
        code: str,
        message: str,
        data: dict = None,
    ):
        self.status_code = status_code
        self.request_id = request_id
        self.code = code
        self.message = message
        self.data = data or {}
        
        detail_msg = f"[{self.code}] {self.message} (Status: {self.status_code}, Request ID: {self.request_id})"
        if self.data:
            detail_msg += f" - Data: {self.data}"
            
        super().__init__(detail_msg)
