from typing import List, Optional, Type

from blacksmith.domain.exceptions import UnregisteredResourceException
from blacksmith.domain.model.http import HTTPTimeout
from blacksmith.domain.model.params import CollectionParser
from blacksmith.domain.registry import Registry, Resources
from blacksmith.domain.registry import registry as default_registry
from blacksmith.middleware._async.base import AsyncHTTPMiddleware
from blacksmith.sd._async.base import AsyncAbstractServiceDiscovery
from blacksmith.service._async.adapters.httpx import AsyncHttpxTransport
from blacksmith.typing import ClientName, ResourceName, Url

from .base import AsyncAbstractTransport
from .route_proxy import (
    AsyncRouteProxy,
    ClientTimeout,
    HTTPAuthentication,
    build_timeout,
)


class AsyncClient:
    """
    Client representation for the client name.

    A client will have dymanic property, based on the registered resources.
    """

    name: ClientName
    endpoint: Url
    resources: Resources
    transport: AsyncAbstractTransport
    timeout: HTTPTimeout
    collection_parser: Type[CollectionParser]
    middlewares: List[AsyncHTTPMiddleware]

    def __init__(
        self,
        name: ClientName,
        endpoint: Url,
        resources: Resources,
        transport: AsyncAbstractTransport,
        timeout: HTTPTimeout,
        collection_parser: Type[CollectionParser],
        middlewares: List[AsyncHTTPMiddleware],
    ) -> None:
        self.name = name
        self.endpoint = endpoint
        self.resources = resources
        self.transport = transport
        self.timeout = timeout
        self.collection_parser = collection_parser
        self.middlewares = middlewares

    def __getattr__(self, name: ResourceName) -> AsyncRouteProxy:
        """
        The client has attributes that are the registered resource.

        The resource are registered using the :func:`blacksmith.register` function.
        """
        try:
            return AsyncRouteProxy(
                self.name,
                name,
                self.endpoint,
                self.resources[name],
                self.transport,
                self.timeout,
                self.collection_parser,
                self.middlewares,
            )
        except KeyError:
            raise UnregisteredResourceException(name, self.name)


class AsyncClientFactory:
    """
    Client creator, for the given configuration.

    :param sd: Service Discovery instance.
    :param transport: HTTP Client that process the call,
        default use :class:`blacksmith.service._async.adapters.httpx.HttpxTransport`
    :param registry: :registy where the resources has been registered.
        default use :data:`blacksmith.domain.registry.registry`
    :param metrics: a metrics collector.
    """

    sd: AsyncAbstractServiceDiscovery
    registry: Registry
    transport: AsyncAbstractTransport
    auth: HTTPAuthentication
    timeout: HTTPTimeout
    collection_parser: Type[CollectionParser]
    middlewares: List[AsyncHTTPMiddleware]

    def __init__(
        self,
        sd: AsyncAbstractServiceDiscovery,
        transport: AsyncAbstractTransport = None,
        registry: Registry = default_registry,
        timeout: ClientTimeout = HTTPTimeout(),
        collection_parser: Type[CollectionParser] = CollectionParser,
    ) -> None:
        self.sd = sd
        self.registry = registry
        self.transport = transport or AsyncHttpxTransport()
        self.timeout = build_timeout(timeout)
        self.collection_parser = collection_parser
        self.middlewares = []
        self._initialized = False

    def add_middleware(self, middleware: AsyncHTTPMiddleware) -> "AsyncClientFactory":
        """
        Add a middleware to the client factory and return the client for chaining.

        ..note:: Clients created before the call of this method will also be
            altered. The middleware stack is a reference for all clients.
        """
        self.middlewares.insert(0, middleware)
        return self

    async def initialize(self):
        for middleware in self.middlewares:
            await middleware.initialize()

    async def __call__(
        self, client_name: ClientName, auth: Optional[HTTPAuthentication] = None
    ):
        if not self._initialized:
            self._initialized = True
            await self.initialize()
        srv, resources = self.registry.get_service(client_name)
        endpoint = await self.sd.get_endpoint(srv[0], srv[1])
        return AsyncClient(
            client_name,
            endpoint,
            resources,
            self.transport,
            self.timeout,
            self.collection_parser,
            self.middlewares,
        )
