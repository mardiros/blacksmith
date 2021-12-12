import time
from typing import Any, Dict, List, Optional, Tuple, Type, Union, cast

from pydantic.typing import NoneType

from blacksmith.domain.exceptions import (
    HTTPError,
    NoContractException,
    UnregisteredRouteException,
    WrongRequestTypeException,
)
from blacksmith.domain.model import (
    CollectionIterator,
    CollectionParser,
    HTTPRequest,
    HTTPResponse,
    HTTPTimeout,
    Request,
    Response,
    ResponseBox,
    TResponse,
)
from blacksmith.domain.registry import ApiRoutes, HttpResource
from blacksmith.middleware.base import HTTPMiddleware, Middleware
from blacksmith.typing import ClientName, HttpMethod, Path, ResourceName, Url

from .base import AbstractTransport

ClientTimeout = Union[HTTPTimeout, float, Tuple[float, float]]
HTTPAuthentication = HTTPMiddleware


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
    timeout: HTTPTimeout
    collection_parser: Type[CollectionParser]
    middlewares: List[HTTPMiddleware]

    def __init__(
        self,
        client_name: ClientName,
        name: ResourceName,
        endpoint: Url,
        routes: ApiRoutes,
        transport: AbstractTransport,
        timeout: HTTPTimeout,
        collection_parser: Type[CollectionParser],
        middlewares: List[HTTPMiddleware],
    ) -> None:
        self.client_name = client_name
        self.name = name
        self.endpoint = endpoint
        self.routes = routes
        self.transport = transport
        self.timeout = timeout
        self.collection_parser = collection_parser
        self.middlewares = middlewares

    def _prepare_request(
        self,
        method: HttpMethod,
        params: Union[Optional[Request], Dict[Any, Any]],
        resource: Optional[HttpResource],
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

    async def _handle_req_with_middlewares(
        self,
        method: HttpMethod,
        req: HTTPRequest,
        timeout: HTTPTimeout,
        path: Path,
    ) -> HTTPResponse:
        async def handle_req(
            req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
        ) -> HTTPResponse:
            return await self.transport.request(method, req, timeout)

        next = cast(Middleware, handle_req)

        for middleware in self.middlewares:
            next = middleware(next)

        resp = await next(req, method, self.client_name, path)
        return resp

    async def _yield_collection_request(
        self,
        method: HttpMethod,
        params: Union[Optional[Request], Dict[Any, Any]],
        timeout: HTTPTimeout,
        path: Path,
    ) -> CollectionIterator:
        req, resp_schema = self._prepare_request(method, params, self.routes.collection)
        resp = await self._handle_req_with_middlewares(method, req, timeout, path)
        return self._prepare_collection_response(
            resp, resp_schema, self.routes.collection.collection_parser
        )

    async def _collection_request(
        self,
        method: HttpMethod,
        params: Union[Request, Dict[Any, Any]],
        timeout: HTTPTimeout,
    ) -> ResponseBox:
        req, resp_schema = self._prepare_request(method, params, self.routes.collection)
        resp = await self._handle_req_with_middlewares(
            method, req, timeout, self.routes.collection.path
        )
        return self._prepare_response(resp, resp_schema, method, self.routes.collection)

    async def _request(
        self,
        method: HttpMethod,
        params: Union[Request, Dict[Any, Any]],
        timeout: HTTPTimeout,
    ) -> ResponseBox:
        req, resp_schema = self._prepare_request(method, params, self.routes.resource)
        resp = await self._handle_req_with_middlewares(
            method,
            req,
            timeout,
            self.routes.resource.path,
        )
        return self._prepare_response(resp, resp_schema, method, self.routes.resource)

    async def collection_head(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._collection_request(
            "HEAD", params, build_timeout(timeout or self.timeout)
        )

    async def collection_get(
        self,
        params: Union[Optional[Request], Dict[Any, Any]] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> CollectionIterator:
        return await self._yield_collection_request(
            "GET",
            params,
            build_timeout(timeout or self.timeout),
            self.routes.collection.path,
        )

    async def collection_post(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._collection_request(
            "POST", params, build_timeout(timeout or self.timeout)
        )

    async def collection_put(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._collection_request(
            "PUT", params, build_timeout(timeout or self.timeout)
        )

    async def collection_patch(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._collection_request(
            "PATCH", params, build_timeout(timeout or self.timeout)
        )

    async def collection_delete(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._collection_request(
            "DELETE", params, build_timeout(timeout or self.timeout)
        )

    async def collection_options(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._collection_request(
            "OPTIONS", params, build_timeout(timeout or self.timeout)
        )

    async def head(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._request(
            "HEAD", params, build_timeout(timeout or self.timeout)
        )

    async def get(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        resp = await self._request(
            "GET", params, build_timeout(timeout or self.timeout)
        )
        return resp

    async def post(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._request(
            "POST", params, build_timeout(timeout or self.timeout)
        )

    async def put(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._request(
            "PUT", params, build_timeout(timeout or self.timeout)
        )

    async def patch(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._request(
            "PATCH", params, build_timeout(timeout or self.timeout)
        )

    async def delete(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._request(
            "DELETE", params, build_timeout(timeout or self.timeout)
        )

    async def options(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return await self._request(
            "OPTIONS", params, build_timeout(timeout or self.timeout)
        )
