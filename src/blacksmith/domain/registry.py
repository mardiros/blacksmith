"""Register resources on services."""

from collections import defaultdict
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any, TypeVar

from blacksmith.typing import (
    ClientName,
    HTTPMethod,
    Path,
    ResourceName,
    Service,
    ServiceName,
    Version,
)

from .exceptions import ConfigurationError, UnregisteredClientException
from .model import AbstractCollectionParser, Request, TCollectionResponse, TResponse

TRequest = TypeVar("TRequest", bound=Request)

Schemas = tuple[TRequest, TResponse]
Contract = Mapping[HTTPMethod, Schemas[Any, Any]]

CollectionSchemas = tuple[TRequest, TCollectionResponse]
CollectionContract = Mapping[HTTPMethod, Schemas[Any, Any]]


@dataclass(frozen=True)
class HttpResource:
    """Represent a resource endpoint."""

    path: Path
    """Path that identify the resource."""
    contract: Contract | None
    """A contract is a serialization schema for the request and there response."""


@dataclass(frozen=True)
class HttpCollection(HttpResource):
    collection_parser: type[AbstractCollectionParser] | None
    """Override the default collection parlser for a given resource."""


class ApiRoutes:
    """
    Store different routes for a type of resource.

    Api may have a route for the resource and/or a route for collection.
    They both have distinct contract for every http method.
    """

    resource: HttpResource | None
    """Resource endpoint"""
    collection: HttpCollection | None
    """Collection endpoint."""

    def __init__(
        self,
        path: Path | None,
        contract: Contract | None,
        collection_path: Path | None,
        collection_contract: Contract | None,
        collection_parser: type[AbstractCollectionParser] | None,
    ) -> None:
        self.resource = HttpResource(path, contract) if path else None
        self.collection = (
            HttpCollection(collection_path, collection_contract, collection_parser)
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
        path: Path | None = None,
        contract: Contract | None = None,
        collection_path: Path | None = None,
        collection_contract: Contract | None = None,
        collection_parser: type[AbstractCollectionParser] | None = None,
    ) -> None:
        """
        Register the resource in the registry.

        :param client_name: used to identify the client in your code.
        :param resource: name of the resource in your code.
        :param service: name of the service in the service discovery.
        :param version: version number of the service.
        :param path: endpoint of the resource in the given service.
        :param contract: contract for the resource, define request and response.

        :param collection_path: endpoint of the resource collection
            in the given service.
        :param collection_contract: contract for the resource collection,
            define request and response.
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
            collection_parser,
        )

    def get_service(self, client_name: ClientName) -> tuple[Service, Resources]:
        """
        Get the service associated for the client.

        This method is used to find the endpoint of the service.
        """
        try:
            return self.client_service[client_name], self.clients[client_name]
        except KeyError as exc:
            raise UnregisteredClientException(client_name) from exc


registry = Registry()
"""Detault registry."""


def register(
    client_name: ClientName,
    resource: ResourceName,
    service: ServiceName,
    version: Version,
    path: Path | None = None,
    contract: Contract | None = None,
    collection_path: Path | None = None,
    collection_contract: CollectionContract | None = None,
    collection_parser: type[AbstractCollectionParser] | None = None,
) -> None:
    """
    Register a resource in a client in the default registry.

    See :func:`blacksmith.domain.registry.Registry.register` for the signature.
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
        collection_parser,
    )
