"""Register resources on services."""


from collections import defaultdict
from typing import Mapping, MutableMapping, Optional, Tuple, Type, cast

from aioli.typing import (
    ClientName,
    HttpMethod,
    Path,
    ResourceName,
    Service,
    ServiceName,
    Version,
)

from .exceptions import ConfigurationError, UnregisteredClientException
from .model import Request, Response

Schemas = Tuple[Type[Request], Optional[Type[Response]]]
Contract = Mapping[HttpMethod, Schemas]


class HttpResource:
    """Represent a resource endpoint."""

    path: Path
    """Path that identify the resource."""
    contract: Optional[Contract]
    """A contract is a serialization schema for the request and there response."""

    def __init__(
        self,
        path: Path,
        contract: Optional[Contract],
    ) -> None:
        self.path = path
        self.contract = contract


class ApiRoutes:
    """
    Store different routes for a type of resource.

    Api may have a route for the resource and/or a route for collection.
    They both have distinct contract for every http method.
    """

    resource: Optional[HttpResource]
    """Resource endpoint"""
    collection: Optional[HttpResource]
    """Collection endpoint."""

    def __init__(
        self,
        path: Optional[Path],
        contract: Optional[Contract],
        collection_path: Optional[Path],
        collection_contract: Optional[Contract],
    ) -> None:
        self.resource = HttpResource(path, contract) if path else None
        self.collection = (
            HttpResource(collection_path, collection_contract)
            if collection_path
            else None
        )


Resources = Mapping[ResourceName, ApiRoutes]


class Registry:
    """Store resources in a registry."""

    clients: MutableMapping[ClientName, MutableMapping[ResourceName, ApiRoutes]]
    client_service: MutableMapping[ClientName, Service]

    def __init__(self) -> None:
        self.clients = defaultdict(dict)
        self.client_service = {}

    def register(
        self,
        client_name: ClientName,
        resource: ResourceName,
        service: ServiceName,
        version: Version,
        path: Optional[Path] = None,
        contract: Optional[Contract] = None,
        collection_path: Optional[Path] = None,
        collection_contract: Optional[Contract] = None,
    ):
        """
        Register the resource in the registry.

        :param client_name: Used to identify the client in your code.
        :param resource: Name of the resource in your code.
        :param service: Name of the service in the service discovery.
        :param version: Version Number of the service.
        :param path: Endpoint of the resource in the given service.
        :param contract: contract for the resource, define request and response.

        :param collection_path: Endpoint of the resource collection in the given service.
        :param collection_contract: contract for the resource collection, define request and response.
        """
        if client_name in self.client_service and self.client_service[client_name] != (
            service,
            version,
        ):
            raise ConfigurationError(
                client_name, self.client_service[client_name], (service, version)
            )

        self.client_service[client_name] = (service, version)
        self.clients[client_name][resource] = ApiRoutes(
            path,
            contract,
            collection_path,
            collection_contract,
        )

    def get_service(self, client_name: ClientName) -> Tuple[Service, Resources]:
        """
        Get the service associated for the client.

        This method is used to find the endpoint of the service.
        """
        try:
            return self.client_service[client_name], self.clients[client_name]
        except KeyError as k:
            raise UnregisteredClientException(client_name)


registry = Registry()
"""Detault registry."""


def register(
    client_name: ClientName,
    resource: ResourceName,
    service: ServiceName,
    version: Version,
    path: Optional[Path] = None,
    contract: Optional[Contract] = None,
    collection_path: Optional[Path] = None,
    collection_contract: Optional[Contract] = None,
):
    """
    Register a resource in a client in the default registry.

    See :func:`aioli.domain.registry.Registry.register` for the signature.
    """
    registry.register(
        client_name,
        resource,
        service,
        version,
        path,
        contract,
        collection_path,
        collection_contract,
    )
