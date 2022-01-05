from typing import List, Optional, Type

from blacksmith.domain.exceptions import UnregisteredResourceException
from blacksmith.domain.model.http import HTTPTimeout
from blacksmith.domain.model.params import CollectionParser
from blacksmith.domain.registry import Registry, Resources
from blacksmith.domain.registry import registry as default_registry
from blacksmith.middleware._sync.base import SyncHTTPMiddleware
from blacksmith.sd._sync.base import SyncAbstractServiceDiscovery
from blacksmith.service._sync.adapters.httpx import SyncHttpxTransport
from blacksmith.typing import ClientName, ResourceName, Url

from .base import SyncAbstractTransport
from .route_proxy import (
    ClientTimeout,
    HTTPAuthentication,
    SyncRouteProxy,
    build_timeout,
)


class SyncClient:
    """
    Client representation for the client name.

    A client will have dymanic property, based on the registered resources.
    """

    name: ClientName
    endpoint: Url
    resources: Resources
    transport: SyncAbstractTransport
    timeout: HTTPTimeout
    collection_parser: Type[CollectionParser]
    middlewares: List[SyncHTTPMiddleware]

    def __init__(
        self,
        name: ClientName,
        endpoint: Url,
        resources: Resources,
        transport: SyncAbstractTransport,
        timeout: HTTPTimeout,
        collection_parser: Type[CollectionParser],
        middlewares: List[SyncHTTPMiddleware],
    ) -> None:
        self.name = name
        self.endpoint = endpoint
        self.resources = resources
        self.transport = transport
        self.timeout = timeout
        self.collection_parser = collection_parser
        self.middlewares = middlewares

    def __getattr__(self, name: ResourceName) -> SyncRouteProxy:
        """
        The client has attributes that are the registered resource.

        The resource are registered using the :func:`blacksmith.register` function.
        """
        try:
            return SyncRouteProxy(
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


class SyncClientFactory:
    """
    Client creator, for the given configuration.

    :param sd: Service Discovery instance.
    :param transport: HTTP Client that process the call,
        default use :class:`blacksmith.service._async.adapters.httpx.HttpxTransport`
    :param registry: :registy where the resources has been registered.
        default use :data:`blacksmith.domain.registry.registry`
    :param metrics: a metrics collector.
    """

    sd: SyncAbstractServiceDiscovery
    registry: Registry
    transport: SyncAbstractTransport
    auth: HTTPAuthentication
    timeout: HTTPTimeout
    collection_parser: Type[CollectionParser]
    middlewares: List[SyncHTTPMiddleware]

    def __init__(
        self,
        sd: SyncAbstractServiceDiscovery,
        transport: SyncAbstractTransport = None,
        registry: Registry = default_registry,
        timeout: ClientTimeout = HTTPTimeout(),
        collection_parser: Type[CollectionParser] = CollectionParser,
    ) -> None:
        self.sd = sd
        self.registry = registry
        self.transport = transport or SyncHttpxTransport()
        self.timeout = build_timeout(timeout)
        self.collection_parser = collection_parser
        self.middlewares = []
        self._initialized = False

    def add_middleware(self, middleware: SyncHTTPMiddleware) -> "SyncClientFactory":
        """
        Add a middleware to the client factory and return the client for chaining.

        ..note:: Clients created before the call of this method will also be
            altered. The middleware stack is a reference for all clients.
        """
        self.middlewares.insert(0, middleware)
        return self

    def initialize(self):
        for middleware in self.middlewares:
            middleware.initialize()

    def __call__(
        self, client_name: ClientName, auth: Optional[HTTPAuthentication] = None
    ):
        if not self._initialized:
            self._initialized = True
            self.initialize()
        srv, resources = self.registry.get_service(client_name)
        endpoint = self.sd.get_endpoint(srv[0], srv[1])
        return SyncClient(
            client_name,
            endpoint,
            resources,
            self.transport,
            self.timeout,
            self.collection_parser,
            self.middlewares,
        )
