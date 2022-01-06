import abc

from blacksmith.typing import ServiceName, Url, Version


class AsyncAbstractServiceDiscovery(abc.ABC):
    """Define the Service Discovery interface."""

    @abc.abstractmethod
    async def get_endpoint(self, service: ServiceName, version: Version) -> Url:
        """Get the endpoint of a service."""
