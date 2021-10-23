import abc
from typing import Optional

Url = str



class AbtractServiceDiscovery(abc.ABC):
    """Define the Service Discovery interface."""

    @abc.abstractmethod
    async def get_endpoint(self, service: str, version: Optional[str]) -> Url:
        """Get the endpoint of a service."""
