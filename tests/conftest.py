import pytest
from tossinvest.client import TossInvestClient


@pytest.fixture
def mock_client():
    """Returns a client initialized with test credentials."""
    return TossInvestClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
        base_url="https://openapi.tossinvest.com",
    )
