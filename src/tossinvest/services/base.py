class BaseService:
    """Base class for all TossInvest services."""

    def __init__(self, client) -> None:
        """Initialize the service with a client instance.

        Args:
            client: An instance of TossInvestClient.
        """
        self.client = client
