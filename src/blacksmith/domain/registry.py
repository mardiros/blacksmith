"""Register resources on services."""


from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Generic, Mapping, MutableMapping, Optional, Tuple, Type

from blacksmith.domain.model.params import TCollec_co, TReq_co, TResp_co
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
from .model import AbstractCollectionParser

Schemas = Tuple[Type[TReq_co], Optional[Type[TResp_co]]]
Contract = Mapping[HTTPMethod, Schemas[TReq_co, TResp_co]]


@dataclass(frozen=True)
class HttpResource(Generic[TReq_co, TResp_co]):
    """Represent a resource endpoint."""

    path: Path
    """Path that identify the resource."""
    contract: Optional[Contract[TReq_co, TResp_co]]
    """A contract is a serialization schema for the request and there response."""


@dataclass(frozen=True)
class HttpCollection(HttpResource[TReq_co, TCollec_co]):
    collection_parser: Optional[Type[AbstractCollectionParser]]
    """Override the default collection parlser for a given resource."""


class ApiRoutes(Generic[TReq_co, TCollec_co, TResp_co]):
    """
    Store different routes for a type of resource.

    Api may have a route for the resource and/or a route for collection.
    They both have distinct contract for every http method.
    """

    resource: Optional[HttpResource[TReq_co, TResp_co]]
    """Resource endpoint"""
    collection: Optional[HttpCollection[TReq_co, TCollec_co]]
    """Collection endpoint."""

    def __init__(
        self,
        path: Optional[Path],
        contract: Optional[Contract[TReq_co, TResp_co]],
        collection_path: Optional[Path],
        collection_contract: Optional[Contract[TReq_co, TCollec_co]],
        collection_parser: Optional[Type[AbstractCollectionParser]],
    ) -> None:
        self.resource = HttpResource(path, contract) if path else None
        self.collection = (
            HttpCollection[TReq_co, TCollec_co](
                collection_path, collection_contract, collection_parser
            )
            if collection_path
            else None
        )


Resources = Mapping[ResourceName, ApiRoutes[Any, Any, Any]]


class Registry:
    """Store resources in a registry."""

    clients: MutableMapping[
        ClientName, MutableMapping[ResourceName, ApiRoutes[Any, Any, Any]]
    ]
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
        contract: Optional[Contract[Any, Any]] = None,
        collection_path: Optional[Path] = None,
        collection_contract: Optional[Contract[Any, Any]] = None,
        collection_parser: Optional[Type[AbstractCollectionParser]] = None,
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

    def get_service(self, client_name: ClientName) -> Tuple[Service, Resources]:
        """
        Get the service associated for the client.

        This method is used to find the endpoint of the service.
        """
        try:
            return self.client_service[client_name], self.clients[client_name]
        except KeyError:
            raise UnregisteredClientException(client_name)


registry = Registry()
"""Detault registry."""


def register(
    client_name: ClientName,
    resource: ResourceName,
    service: ServiceName,
    version: Version,
    path: Optional[Path] = None,
    contract: Optional[Contract[Any, Any]] = None,
    collection_path: Optional[Path] = None,
    collection_contract: Optional[Contract[Any, Any]] = None,
    collection_parser: Optional[Type[AbstractCollectionParser]] = None,
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
