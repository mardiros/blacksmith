import time
from typing import Any, Dict, List, Optional, Tuple, Type, Union, cast

from pydantic.typing import NoneType

from aioli.monitoring.base import AbstractMetricsCollector, SinkholeMetrics
from aioli.service.adapters.httpx import HttpxTransport

from ..domain.exceptions import (
    HTTPError,
    NoContractException,
    UnregisteredResourceException,
    UnregisteredRouteException,
    WrongRequestTypeException,
)
from ..domain.model import (
    CollectionIterator,
    CollectionParser,
    HTTPAuthentication,
    HTTPMiddleware,
    HTTPRequest,
    HTTPResponse,
    HTTPTimeout,
    HTTPUnauthenticated,
    Request,
    Response,
    ResponseBox,
    TResponse,
)
from ..domain.registry import ApiRoutes, HttpResource, Registry, Resources
from ..domain.registry import registry as default_registry
from ..sd.base import AbstractServiceDiscovery
from ..typing import ClientName, HttpMethod, Path, ResourceName, Url
from .base import AbstractTransport

ClientTimeout = Union[HTTPTimeout, float, Tuple[float, float]]


def build_timeout(timeout: ClientTimeout) -> HTTPTimeout:
    """Build the timeout from the convenient timeout."""
    if isinstance(timeout, float):
        timeout = HTTPTimeout(timeout)
    elif isinstance(timeout, tuple):
        timeout = HTTPTimeout(*timeout)
    return timeout


class RouteProxy:
    """Proxy from resource to its associate routes."""

    client_name: ClientName
    name: ResourceName
    endpoint: Url
    routes: ApiRoutes
    transport: AbstractTransport
    auth: HTTPAuthentication
    timeout: HTTPTimeout
    collection_parser: Type[CollectionParser]
    metrics: AbstractMetricsCollector
    middlewares: List[HTTPMiddleware]

    def __init__(
        self,
        client_name: ClientName,
        name: ResourceName,
        endpoint: Url,
        routes: ApiRoutes,
        transport: AbstractTransport,
        auth: HTTPAuthentication,
        timeout: HTTPTimeout,
        collection_parser: Type[CollectionParser],
        metrics: AbstractMetricsCollector,
        middlewares: List[HTTPMiddleware],
    ) -> None:
        self.client_name = client_name
        self.name = name
        self.endpoint = endpoint
        self.routes = routes
        self.transport = transport
        self.auth = auth
        self.timeout = timeout
        self.collection_parser = collection_parser
        self.metrics = metrics
        self.middlewares = middlewares

    def _prepare_request(
        self,
        method: HttpMethod,
        params: Union[Optional[Request], Dict[Any, Any]],
        resource: Optional[HttpResource],
        auth: HTTPAuthentication,
    ) -> Tuple[HTTPRequest, Union[NoneType, Type[TResponse]]]:
        if resource is None:
            raise UnregisteredRouteException(method, self.name, self.client_name)
        if resource.contract is None or method not in resource.contract:
            raise NoContractException(method, self.name, self.client_name)

        param_schema, return_schema = resource.contract[method]
        if isinstance(params, dict):
            params = param_schema(**params)
        elif params is None:
            params = param_schema()
        elif not isinstance(params, param_schema):
            raise WrongRequestTypeException(
                params.__class__, method, self.name, self.client_name
            )
        req = params.to_http_request(self.endpoint + resource.path)
        for middleware in self.middlewares:
            req = req.merge_middleware(middleware)
        req = req.merge_middleware(auth)
        return (req, return_schema)

    def _prepare_response(
        self,
        response: HTTPResponse,
        response_schema: Optional[Type[Response]],
        method: HttpMethod,
        resource: Optional[HttpResource],
    ) -> ResponseBox:
        return ResponseBox(
            response,
            response_schema,
            method,
            resource.path,
            self.name,
            self.client_name,
        )

    def _prepare_collection_response(
        self,
        response: HTTPResponse,
        response_schema: Optional[Type[Response]],
        collection_parser: Optional[Type[CollectionParser]],
    ) -> CollectionIterator:

        return CollectionIterator(
            response, response_schema, collection_parser or self.collection_parser
        )

    async def _yield_collection_request(
        self,
        method: HttpMethod,
        params: Union[Optional[Request], Dict[Any, Any]],
        auth: HTTPAuthentication,
        timeout: HTTPTimeout,
    ) -> CollectionIterator:
        req, resp_schema = self._prepare_request(
            method, params, self.routes.collection, auth
        )
        resp = await self.transport.request(method, req, timeout)
        return self._prepare_collection_response(
            resp, resp_schema, self.routes.collection.collection_parser
        )

    async def _collection_request(
        self,
        method: HttpMethod,
        params: Union[Request, Dict[Any, Any]],
        auth: HTTPAuthentication,
        timeout: HTTPTimeout,
    ) -> ResponseBox:
        status_code = 0
        start = time.perf_counter()
        try:
            req, resp_schema = self._prepare_request(
                method, params, self.routes.collection, auth
            )
            resp = await self.transport.request(method, req, timeout)
            status_code = resp.status_code
            resp = self._prepare_response(
                resp, resp_schema, method, self.routes.collection
            )
        except HTTPError as exc:
            status_code = exc.response.status_code
            raise exc
        finally:
            if status_code > 0:
                self.metrics.observe_request(
                    self.client_name,
                    method,
                    self.routes.collection.path,
                    status_code,
                    time.perf_counter() - start,
                )
        return resp

    async def _request(
        self,
        method: HttpMethod,
        params: Union[Request, Dict[Any, Any]],
        auth: HTTPAuthentication,
        timeout: HTTPTimeout,
    ) -> ResponseBox:
        status_code = 0
        start = time.perf_counter()
        try:
            req, resp_schema = self._prepare_request(
                method, params, self.routes.resource, auth
            )
            resp = await self.transport.request(method, req, timeout)
            status_code = resp.status_code
            resp = self._prepare_response(
                resp, resp_schema, method, self.routes.resource
            )
        except HTTPError as exc:
            status_code = exc.response.status_code
            raise exc
        finally:
            if status_code > 0:
                self.metrics.observe_request(
                    self.client_name,
                    method,
                    self.routes.resource.path,
                    status_code,
                    time.perf_counter() - start,
                )
        return resp

    async def collection_head(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._collection_request(
            "HEAD", params, auth or self.auth, build_timeout(timeout or self.timeout)
        )

    async def collection_get(
        self,
        params: Union[Optional[Request], Dict[Any, Any]] = None,
        auth: Optional[HTTPAuthentication] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> CollectionIterator:
        return await self._yield_collection_request(
            "GET", params, auth or self.auth, build_timeout(timeout or self.timeout)
        )

    async def collection_post(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._collection_request(
            "POST", params, auth or self.auth, build_timeout(timeout or self.timeout)
        )

    async def collection_put(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._collection_request(
            "PUT", params, auth or self.auth, build_timeout(timeout or self.timeout)
        )

    async def collection_patch(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._collection_request(
            "PATCH", params, auth or self.auth, build_timeout(timeout or self.timeout)
        )

    async def collection_delete(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._collection_request(
            "DELETE", params, auth or self.auth, build_timeout(timeout or self.timeout)
        )

    async def collection_options(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._collection_request(
            "OPTIONS", params, auth or self.auth, build_timeout(timeout or self.timeout)
        )

    async def head(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._request(
            "HEAD", params, auth or self.auth, build_timeout(timeout or self.timeout)
        )

    async def get(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        resp = await self._request(
            "GET", params, auth or self.auth, build_timeout(timeout or self.timeout)
        )
        return resp

    async def post(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._request(
            "POST", params, auth or self.auth, build_timeout(timeout or self.timeout)
        )

    async def put(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._request(
            "PUT", params, auth or self.auth, build_timeout(timeout or self.timeout)
        )

    async def patch(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._request(
            "PATCH", params, auth or self.auth, build_timeout(timeout or self.timeout)
        )

    async def delete(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._request(
            "DELETE", params, auth or self.auth, build_timeout(timeout or self.timeout)
        )

    async def options(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._request(
            "OPTIONS", params, auth or self.auth, build_timeout(timeout or self.timeout)
        )


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
    metrics: AbstractMetricsCollector
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
        metrics: AbstractMetricsCollector,
        middlewares: List[HTTPMiddleware],
    ) -> None:
        self.name = name
        self.endpoint = endpoint
        self.resources = resources
        self.transport = transport
        self.auth = auth
        self.timeout = timeout
        self.collection_parser = collection_parser
        self.metrics = metrics
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
                self.metrics,
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
    metrics: AbstractMetricsCollector
    middlewares: List[HTTPMiddleware]

    def __init__(
        self,
        sd: AbstractServiceDiscovery,
        auth: HTTPAuthentication = HTTPUnauthenticated(),
        transport: AbstractTransport = None,
        registry: Registry = default_registry,
        timeout: ClientTimeout = HTTPTimeout(),
        collection_parser: Type[CollectionParser] = CollectionParser,
        metrics: AbstractMetricsCollector = SinkholeMetrics(),
    ) -> None:
        self.sd = sd
        self.registry = registry
        self.transport = transport or HttpxTransport()
        self.auth = auth
        self.timeout = build_timeout(timeout)
        self.collection_parser = collection_parser
        self.metrics = metrics
        self.middlewares = []

    def add_middleware(self, middleware: HTTPMiddleware):
        """
        Add a middleware to the client factory.

        ..note:: Clients created before the call of this method will also be
            altered. The middleware stack is a reference for all clients.
        """
        self.middlewares.append(middleware)

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
            self.metrics,
            self.middlewares,
        )
