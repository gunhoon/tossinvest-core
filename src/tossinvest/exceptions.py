from typing import Optional, Any, Dict

class TossInvestError(Exception):
    """Base exception for all errors in the tossinvest package."""
    pass

class TossInvestAPIError(TossInvestError):
    """Exception raised when the Toss Investment API returns a non-2xx status code."""
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        request_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.request_id = request_id
        self.data = data or {}
        
        err_msg = f"[{status_code}] {code}: {message}"
        if request_id:
            err_msg += f" (Request ID: {request_id})"
        if self.data:
            err_msg += f" - Data: {self.data}"
            
        super().__init__(err_msg)

class InvalidRequestError(TossInvestAPIError):
    """400 Bad Request: Request is invalid or missing required parameters."""
    pass

class AuthenticationError(TossInvestAPIError):
    """401 Unauthorized: Invalid, expired, or missing tokens."""
    pass

class ForbiddenError(TossInvestAPIError):
    """403 Forbidden: Missing permission or IP blocked."""
    pass

class NotFoundError(TossInvestAPIError):
    """404 Not Found: Stock, account, order, or route not found."""
    pass

class ConflictError(TossInvestAPIError):
    """409 Conflict: Duplicated request or order state conflicts."""
    pass

class UnprocessableEntityError(TossInvestAPIError):
    """422 Unprocessable Entity: Business logic validation failure (e.g. buying power, hours)."""
    pass

class RateLimitExceeded(TossInvestAPIError):
    """429 Too Many Requests: Rate limit exceeded."""
    pass

class InternalServerError(TossInvestAPIError):
    """500 Internal Server Error: Toss server maintenance or error."""
    pass

def raise_for_status(status_code: int, response_json: Optional[Dict[str, Any]] = None, response_headers: Optional[Any] = None) -> None:
    """Helper function to map HTTP status codes to custom exceptions."""
    if 200 <= status_code < 300:
        return
        
    code = "unknown-error"
    message = "An unknown error occurred"
    request_id = None
    data = None
    
    if response_headers:
        request_id = response_headers.get("X-Request-Id")
        
    if response_json and isinstance(response_json, dict) and "error" in response_json:
        err_body = response_json["error"]
        if isinstance(err_body, dict):
            code = err_body.get("code", code)
            message = err_body.get("message", message)
            request_id = err_body.get("requestId", request_id)
            data = err_body.get("data")
            
    # Map status code to specific exceptions
    if status_code == 400:
        raise InvalidRequestError(status_code, code, message, request_id, data)
    elif status_code == 401:
        raise AuthenticationError(status_code, code, message, request_id, data)
    elif status_code == 403:
        raise ForbiddenError(status_code, code, message, request_id, data)
    elif status_code == 404:
        raise NotFoundError(status_code, code, message, request_id, data)
    elif status_code == 409:
        raise ConflictError(status_code, code, message, request_id, data)
    elif status_code == 422:
        raise UnprocessableEntityError(status_code, code, message, request_id, data)
    elif status_code == 429:
        raise RateLimitExceeded(status_code, code, message, request_id, data)
    elif status_code >= 500:
        raise InternalServerError(status_code, code, message, request_id, data)
    else:
        raise TossInvestAPIError(status_code, code, message, request_id, data)
