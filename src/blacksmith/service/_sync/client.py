from typing import Any, Generic

from blacksmith.domain.error import AbstractErrorParser, TError_co, default_error_parser
from blacksmith.domain.exceptions import UnregisteredResourceException
from blacksmith.domain.model.http import HTTPTimeout
from blacksmith.domain.model.params import AbstractCollectionParser, CollectionParser
from blacksmith.domain.registry import Registry, Resources
from blacksmith.domain.registry import registry as default_registry
from blacksmith.middleware._sync.base import SyncHTTPMiddleware
from blacksmith.sd._sync.base import SyncAbstractServiceDiscovery
from blacksmith.service._sync.adapters.httpx import SyncHttpxTransport
from blacksmith.typing import ClientName, Proxies, ResourceName, Url

from .base import SyncAbstractTransport
from .route_proxy import ClientTimeout, SyncRouteProxy, build_timeout

default_timeout = HTTPTimeout()


class SyncClient(Generic[TError_co]):
    """
    Client representation for the client name.

    A client will have dymanic property, based on the registered resources.
    """

    name: ClientName
    endpoint: Url
    resources: Resources
    transport: SyncAbstractTransport
    timeout: HTTPTimeout
    collection_parser: type[AbstractCollectionParser]
    middlewares: list[SyncHTTPMiddleware]

    def __init__(
        self,
        name: ClientName,
        endpoint: Url,
        resources: Resources,
        transport: SyncAbstractTransport,
        timeout: HTTPTimeout,
        collection_parser: type[AbstractCollectionParser],
        middlewares: list[SyncHTTPMiddleware],
        error_parser: AbstractErrorParser[TError_co],
    ) -> None:
        self.name = name
        self.endpoint = endpoint
        self.resources = resources
        self.transport = transport
        self.timeout = timeout
        self.collection_parser = collection_parser
        self.error_parser = error_parser
        self.middlewares = middlewares.copy()

    def add_middleware(self, middleware: SyncHTTPMiddleware) -> "SyncClient[TError_co]":
        self.middlewares.insert(0, middleware)
        return self

    def __getattr__(self, name: ResourceName) -> SyncRouteProxy[Any, Any, TError_co]:
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
                self.error_parser,
                self.middlewares,
            )
        except KeyError as exc:
            raise UnregisteredResourceException(name, self.name) from exc


class SyncClientFactory(Generic[TError_co]):
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
    collection_parser: type[AbstractCollectionParser]
    middlewares: list[SyncHTTPMiddleware]
    error_parser: AbstractErrorParser[TError_co]

    def __init__(
        self,
        sd: SyncAbstractServiceDiscovery,
        transport: SyncAbstractTransport | None = None,
        registry: Registry = default_registry,
        timeout: ClientTimeout = default_timeout,
        proxies: Proxies | None = None,
        verify_certificate: bool = False,
        collection_parser: type[AbstractCollectionParser] = CollectionParser,
        error_parser: AbstractErrorParser[TError_co] | None = None,
    ) -> None:
        self.sd = sd
        self.registry = registry
        self.transport = transport or SyncHttpxTransport(
            verify_certificate=verify_certificate,
            proxies=proxies,
        )
        self.timeout = build_timeout(timeout)
        self.collection_parser = collection_parser
        # no default in TypeVar, wait for https://peps.python.org/pep-0696/
        # so the default_error_parser assume than TError_co, is HTTPError here
        self.error_parser = error_parser or default_error_parser  # type: ignore
        self.middlewares = []

    def add_middleware(
        self, middleware: SyncHTTPMiddleware
    ) -> "SyncClientFactory[TError_co]":
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

    def __call__(self, client_name: ClientName) -> SyncClient[TError_co]:
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
            self.error_parser,
        )
