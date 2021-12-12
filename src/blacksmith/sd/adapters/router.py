"""
The Server-Side Service discovery strategy.

"""
from blacksmith.typing import Service, ServiceName, Version

from ..base import AbstractServiceDiscovery, Url


class RouterDiscovery(AbstractServiceDiscovery):
    """
    Router that implement a :term:`Server-Side Service discovery`.

    This implementatin never raise :class:`blacksmith.domain.exceptions.UnregisteredServiceException`
    when service are unknown, because it only passe very request to the router server
    that is connected to the :term:`service registry`.

    .. note::
        Given pattern in parameter have to match the format of the router server.

    :param service_url_fmt: A pattern used to create endpoint of versionned services.
    :param unversioned_service_url_fmt: A pattern used to create endpoint of unversionned services.
    """

    service_url_fmt: str
    unversioned_service_url_fmt: str

    def __init__(
        self,
        service_url_fmt: str = "http://router/{service}-{version}/{version}",
        unversioned_service_url_fmt: str = "http://router/{service}",
    ) -> None:
        self.service_url_fmt = service_url_fmt
        self.unversioned_service_url_fmt = unversioned_service_url_fmt

    async def get_endpoint(self, service: ServiceName, version: Version) -> Url:
        """
        Create and return the endpoint using the given parameters `service_url_fmt`
        or `unversioned_service_url_fmt` if version is `None`.
        """
        if version is None:
            name = self.unversioned_service_url_fmt.format(service=service)
        else:
            name = self.service_url_fmt.format(service=service, version=version)
        return name
