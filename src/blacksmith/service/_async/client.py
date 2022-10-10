from typing import Any, Generic, List, Optional, Type

from blacksmith.domain.error import AbstractErrorParser, TError_co, default_error_parser
from blacksmith.domain.exceptions import UnregisteredResourceException
from blacksmith.domain.model.http import HTTPTimeout
from blacksmith.domain.model.params import AbstractCollectionParser, CollectionParser
from blacksmith.domain.registry import Registry, Resources
from blacksmith.domain.registry import registry as default_registry
from blacksmith.middleware._async.base import AsyncHTTPMiddleware
from blacksmith.sd._async.base import AsyncAbstractServiceDiscovery
from blacksmith.service._async.adapters.httpx import AsyncHttpxTransport
from blacksmith.typing import ClientName, Proxies, ResourceName, Url

from .base import AsyncAbstractTransport
from .route_proxy import AsyncRouteProxy, ClientTimeout, build_timeout


class AsyncClient(Generic[TError_co]):
    """
    Client representation for the client name.

    A client will have dymanic property, based on the registered resources.
    """

    name: ClientName
    endpoint: Url
    resources: Resources
    transport: AsyncAbstractTransport
    timeout: HTTPTimeout
    collection_parser: Type[AbstractCollectionParser]
    middlewares: List[AsyncHTTPMiddleware]

    def __init__(
        self,
        name: ClientName,
        endpoint: Url,
        resources: Resources,
        transport: AsyncAbstractTransport,
        timeout: HTTPTimeout,
        collection_parser: Type[AbstractCollectionParser],
        middlewares: List[AsyncHTTPMiddleware],
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

    def add_middleware(
        self, middleware: AsyncHTTPMiddleware
    ) -> "AsyncClient[TError_co]":
        self.middlewares.insert(0, middleware)
        return self

    def __getattr__(self, name: ResourceName) -> AsyncRouteProxy[Any, Any, TError_co]:
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
                self.error_parser,
                self.middlewares,
            )
        except KeyError:
            raise UnregisteredResourceException(name, self.name)


class AsyncClientFactory(Generic[TError_co]):
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

    sd: AsyncAbstractServiceDiscovery
    registry: Registry
    transport: AsyncAbstractTransport
    timeout: HTTPTimeout
    collection_parser: Type[AbstractCollectionParser]
    middlewares: List[AsyncHTTPMiddleware]
    error_parser: AbstractErrorParser[TError_co]

    def __init__(
        self,
        sd: AsyncAbstractServiceDiscovery,
        transport: Optional[AsyncAbstractTransport] = None,
        registry: Registry = default_registry,
        timeout: ClientTimeout = HTTPTimeout(),
        proxies: Optional[Proxies] = None,
        verify_certificate: bool = False,
        collection_parser: Type[AbstractCollectionParser] = CollectionParser,
        error_parser: Optional[AbstractErrorParser[TError_co]] = None,
    ) -> None:
        self.sd = sd
        self.registry = registry
        self.transport = transport or AsyncHttpxTransport(
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
        self, middleware: AsyncHTTPMiddleware
    ) -> "AsyncClientFactory[TError_co]":
        """
        Add a middleware to the client factory and return the client for chaining.

        ..note:: Clients created before the call of this method will also be
            altered. The middleware stack is a reference for all clients.
        """
        self.middlewares.insert(0, middleware)
        return self

    async def initialize(self) -> None:
        for middleware in self.middlewares:
            await middleware.initialize()

    async def __call__(self, client_name: ClientName) -> AsyncClient[TError_co]:
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
            self.error_parser,
        )
