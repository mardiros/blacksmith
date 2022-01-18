from typing import Generic, List, Optional, Type

from blacksmith.domain.exceptions import UnregisteredResourceException
from blacksmith.domain.model.http import HTTPTimeout
from blacksmith.domain.model.params import (
    AbstractCollectionParser,
    CollectionParser,
    TCollectionResponse,
    TResponse,
)
from blacksmith.domain.registry import Registry, Resources
from blacksmith.domain.registry import registry as default_registry
from blacksmith.middleware._sync.base import SyncHTTPMiddleware
from blacksmith.sd._sync.base import SyncAbstractServiceDiscovery
from blacksmith.service._sync.adapters.httpx import SyncHttpxTransport
from blacksmith.typing import ClientName, Proxies, ResourceName, Url

from .base import SyncAbstractTransport
from .route_proxy import ClientTimeout, SyncRouteProxy, build_timeout


class SyncClient(Generic[TCollectionResponse, TResponse]):
    """
    Client representation for the client name.

    A client will have dymanic property, based on the registered resources.
    """

    name: ClientName
    endpoint: Url
    resources: Resources
    transport: SyncAbstractTransport
    timeout: HTTPTimeout
    collection_parser: Type[AbstractCollectionParser]
    middlewares: List[SyncHTTPMiddleware]

    def __init__(
        self,
        name: ClientName,
        endpoint: Url,
        resources: Resources,
        transport: SyncAbstractTransport,
        timeout: HTTPTimeout,
        collection_parser: Type[AbstractCollectionParser],
        middlewares: List[SyncHTTPMiddleware],
    ) -> None:
        self.name = name
        self.endpoint = endpoint
        self.resources = resources
        self.transport = transport
        self.timeout = timeout
        self.collection_parser = collection_parser
        self.middlewares = middlewares.copy()

    def add_middleware(
        self, middleware: SyncHTTPMiddleware
    ) -> "SyncClient[TCollectionResponse, TResponse]":
        self.middlewares.insert(0, middleware)
        return self

    def __getattr__(
        self, name: ResourceName
    ) -> SyncRouteProxy[TCollectionResponse, TResponse]:
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


class SyncClientFactory(Generic[TCollectionResponse, TResponse]):
    """
    Client creator, for the given configuration.

    :param sd: Service Discovery instance
    :param transport: HTTP Client that process the call,
        default use :class:`blacksmith.service._async.adapters.httpx.HttpxTransport`
    :param timeout: configure timeout,
        this parameter is ignored if the transport has been passed
    :param proxies: configure proxies,
        this parameter is ignored if the transport has been passed
    :param verify_certificate: Reject request if certificate are invalid for https
    :param collection_parser: use to customize the collection parser
        default use :class:`blacksmith.domain.model.params.CollectionParser`
    """

    sd: SyncAbstractServiceDiscovery
    registry: Registry
    transport: SyncAbstractTransport
    timeout: HTTPTimeout
    collection_parser: Type[AbstractCollectionParser]
    middlewares: List[SyncHTTPMiddleware]

    def __init__(
        self,
        sd: SyncAbstractServiceDiscovery,
        transport: Optional[SyncAbstractTransport] = None,
        registry: Registry = default_registry,
        timeout: ClientTimeout = HTTPTimeout(),
        proxies: Optional[Proxies] = None,
        verify_certificate: bool = False,
        collection_parser: Type[AbstractCollectionParser] = CollectionParser,
    ) -> None:
        self.sd = sd
        self.registry = registry
        self.transport = transport or SyncHttpxTransport(
            verify_certificate=verify_certificate,
            proxies=proxies,
        )
        self.timeout = build_timeout(timeout)
        self.collection_parser = collection_parser
        self.middlewares = []
        self._initialized = False

    def add_middleware(
        self, middleware: SyncHTTPMiddleware
    ) -> "SyncClientFactory[TCollectionResponse,TResponse]":
        """
        Add a middleware to the client factory and return the client for chaining.

        ..note:: Clients created before the call of this method will also be
            altered. The middleware stack is a reference for all clients.
        """
        self.middlewares.insert(0, middleware)
        return self

    def initialize(self) -> None:
        for middleware in self.middlewares:
            middleware.initialize()

    def __call__(
        self, client_name: ClientName
    ) -> SyncClient[TCollectionResponse, TResponse]:
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
