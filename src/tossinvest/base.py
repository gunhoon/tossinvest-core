from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tossinvest.client import TossInvestClient


class APIGroup:
    """Base class for sub-API groups to share the parent client reference."""
    def __init__(self, client: "TossInvestClient"):
        self._client = client
