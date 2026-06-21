import time
from typing import Any, Dict, Optional

from tossinvest.exceptions import TossInvestAuthError
from tossinvest.models import OAuth2TokenResponse
from tossinvest.services.base import BaseService


class AuthService(BaseService):
    """Service to handle authentication, OAuth2 token issuance, and caching lifecycle."""

    def __init__(self, client) -> None:
        """Initialize AuthService.

        Args:
            client: An instance of TossInvestClient.
        """
        super().__init__(client)
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def issue_token(self) -> OAuth2TokenResponse:
        """Manually trigger OAuth2 token issuance.

        Calls the POST /oauth2/token endpoint and updates cache.

        Returns:
            OAuth2TokenResponse containing access_token, token_type, expires_in.
        """
        url = f"{self.client.base_url}/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client.client_id,
            "client_secret": self.client.client_secret,
        }

        try:
            response = self.client.session.post(
                url, headers=headers, data=data, timeout=15
            )
            status_code = response.status_code
            body_text = response.text

            if status_code != 200:
                raise TossInvestAuthError(
                    f"Authentication failed with status code {status_code}: {body_text}",
                    response_body=body_text,
                )

            res_json = response.json()
            self._token = res_json["access_token"]
            expires_in = res_json["expires_in"]
            self._token_expires_at = time.time() + expires_in

            # Construct and return type-conforming dict
            return {
                "access_token": self._token,
                "token_type": "Bearer",
                "expires_in": int(max(0, self._token_expires_at - time.time())),
            }
        except TossInvestAuthError:
            raise
        except Exception as e:
            raise TossInvestAuthError(f"Failed to request OAuth2 token: {e}") from e

    def get_token(self) -> str:
        """Get a valid access token.

        Checks cache and requests a new token if expired.

        Returns:
            The active access token string.
        """
        now = time.time()
        # Add a 60-second safety buffer before token expiration
        if self._token and now < self._token_expires_at - 60:
            return self._token

        self.issue_token()
        assert self._token is not None
        return self._token
