import abc

from ..typing import ServiceName, Url, Version


class AbtractServiceDiscovery(abc.ABC):
    """Define the Service Discovery interface."""

    @abc.abstractmethod
    async def get_endpoint(self, service: ServiceName, version: Version) -> Url:
        """Get the endpoint of a service."""
