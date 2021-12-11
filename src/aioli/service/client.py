from typing import List, Optional, Type

from aioli.domain.exceptions import UnregisteredResourceException
from aioli.domain.model.http import HTTPTimeout
from aioli.domain.model.params import CollectionParser
from aioli.domain.registry import Registry, Resources
from aioli.domain.registry import registry as default_registry
from aioli.middleware.auth import HTTPUnauthenticated
from aioli.middleware.base import HTTPMiddleware
from aioli.sd.base import AbstractServiceDiscovery
from aioli.service.adapters.httpx import HttpxTransport
from aioli.typing import ClientName, ResourceName, Url

from .base import AbstractTransport
from .route_proxy import ClientTimeout, HTTPAuthentication, RouteProxy, build_timeout


class Client:
    """
    Client representation for the client name.

    A client will have dymanic property, based on the registered resources.
    """

    name: ClientName
    endpoint: Url
    resources: Resources
    transport: AbstractTransport
    auth: HTTPAuthentication
    timeout: HTTPTimeout
    collection_parser: Type[CollectionParser]
    middlewares: List[HTTPMiddleware]

    def __init__(
        self,
        name: ClientName,
        endpoint: Url,
        resources: Resources,
        transport: AbstractTransport,
        auth: HTTPAuthentication,
        timeout: HTTPTimeout,
        collection_parser: Type[CollectionParser],
        middlewares: List[HTTPMiddleware],
    ) -> None:
        self.name = name
        self.endpoint = endpoint
        self.resources = resources
        self.transport = transport
        self.auth = auth
        self.timeout = timeout
        self.collection_parser = collection_parser
        self.middlewares = middlewares

    def __getattr__(self, name: ResourceName) -> RouteProxy:
        """
        The client has attributes that are the registered resource.

        The resource are registered using the :func:`aioli.register` function.
        """
        try:
            return RouteProxy(
                self.name,
                name,
                self.endpoint,
                self.resources[name],
                self.transport,
                self.auth,
                self.timeout,
                self.collection_parser,
                self.middlewares,
            )
        except KeyError:
            raise UnregisteredResourceException(name, self.name)


class ClientFactory:
    """
    Client creator, for the given configuration.

    :param sd: Service Discovery instance.
    :param transport: HTTP Client that process the call,
        default use :class:`aioli.service.adapters.httpx.HttpxTransport`
    :param registry: :registy where the resources has been registered.
        default use :data:`aioli.domain.registry.registry`
    :param metrics: a metrics collector.
    """

    sd: AbstractServiceDiscovery
    registry: Registry
    transport: AbstractTransport
    auth: HTTPAuthentication
    timeout: HTTPTimeout
    collection_parser: Type[CollectionParser]
    middlewares: List[HTTPMiddleware]

    def __init__(
        self,
        sd: AbstractServiceDiscovery,
        auth: HTTPAuthentication = HTTPUnauthenticated(),
        transport: AbstractTransport = None,
        registry: Registry = default_registry,
        timeout: ClientTimeout = HTTPTimeout(),
        collection_parser: Type[CollectionParser] = CollectionParser,
    ) -> None:
        self.sd = sd
        self.registry = registry
        self.transport = transport or HttpxTransport()
        self.auth = auth
        self.timeout = build_timeout(timeout)
        self.collection_parser = collection_parser
        self.middlewares = []

    def add_middleware(self, middleware: HTTPMiddleware) -> "ClientFactory":
        """
        Add a middleware to the client factory and return the client for chaining.

        ..note:: Clients created before the call of this method will also be
            altered. The middleware stack is a reference for all clients.
        """
        self.middlewares.append(middleware)
        return self

    async def __call__(
        self, client_name: ClientName, auth: Optional[HTTPAuthentication] = None
    ):
        srv, resources = self.registry.get_service(client_name)
        endpoint = await self.sd.get_endpoint(srv[0], srv[1])
        return Client(
            client_name,
            endpoint,
            resources,
            self.transport,
            auth or self.auth,
            self.timeout,
            self.collection_parser,
            self.middlewares,
        )
