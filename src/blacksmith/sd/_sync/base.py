import abc

from blacksmith.typing import ServiceName, Url, Version


class SyncAbstractServiceDiscovery(abc.ABC):
    """Define the Service Discovery interface."""

    @abc.abstractmethod
    def get_endpoint(self, service: ServiceName, version: Version) -> Url:
        """Get the endpoint of a service."""
