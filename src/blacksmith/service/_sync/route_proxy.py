from typing import Any, Dict, List, Optional, Tuple, Type, Union, cast

from blacksmith.domain.exceptions import (
    NoContractException,
    UnregisteredRouteException,
    WrongRequestTypeException,
)
from blacksmith.domain.model import (
    CollectionIterator,
    HTTPRequest,
    HTTPResponse,
    HTTPTimeout,
    Request,
    Response,
    ResponseBox,
)
from blacksmith.domain.model.params import AbstractCollectionParser
from blacksmith.domain.registry import ApiRoutes, HttpCollection, HttpResource
from blacksmith.middleware._sync.base import SyncHTTPMiddleware, SyncMiddleware
from blacksmith.typing import ClientName, HttpMethod, Path, ResourceName, Url

from .base import SyncAbstractTransport

ClientTimeout = Union[HTTPTimeout, float, Tuple[float, float]]
HTTPAuthentication = SyncHTTPMiddleware


def build_timeout(timeout: ClientTimeout) -> HTTPTimeout:
    """Build the timeout from the convenient timeout."""
    if isinstance(timeout, float):
        timeout = HTTPTimeout(timeout)
    elif isinstance(timeout, tuple):
        timeout = HTTPTimeout(*timeout)
    return timeout


class SyncRouteProxy:
    """Proxy from resource to its associate routes."""

    client_name: ClientName
    name: ResourceName
    endpoint: Url
    routes: ApiRoutes
    transport: SyncAbstractTransport
    timeout: HTTPTimeout
    collection_parser: Type[AbstractCollectionParser]
    middlewares: List[SyncHTTPMiddleware]

    def __init__(
        self,
        client_name: ClientName,
        name: ResourceName,
        endpoint: Url,
        routes: ApiRoutes,
        transport: SyncAbstractTransport,
        timeout: HTTPTimeout,
        collection_parser: Type[AbstractCollectionParser],
        middlewares: List[SyncHTTPMiddleware],
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
    ) -> Tuple[Path, HTTPRequest, Optional[Type[Response]]]:
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
        return (resource.path, req, return_schema)

    def _prepare_response(
        self,
        response: HTTPResponse,
        response_schema: Optional[Type[Response]],
        method: HttpMethod,
        path: Path,
    ) -> ResponseBox:
        return ResponseBox(
            response,
            response_schema,
            method,
            path,
            self.name,
            self.client_name,
        )

    def _prepare_collection_response(
        self,
        response: HTTPResponse,
        response_schema: Optional[Type[Response]],
        collection_parser: Optional[Type[AbstractCollectionParser]],
    ) -> CollectionIterator:

        return CollectionIterator(
            response, response_schema, collection_parser or self.collection_parser
        )

    def _handle_req_with_middlewares(
        self,
        method: HttpMethod,
        req: HTTPRequest,
        timeout: HTTPTimeout,
        path: Path,
    ) -> HTTPResponse:
        def handle_req(
            req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
        ) -> HTTPResponse:
            return self.transport.request(method, req, timeout)

        next = cast(SyncMiddleware, handle_req)

        for middleware in self.middlewares:
            next = middleware(next)

        resp = next(req, method, self.client_name, path)
        return resp

    def _yield_collection_request(
        self,
        method: HttpMethod,
        params: Union[Optional[Request], Dict[Any, Any]],
        timeout: HTTPTimeout,
        collection: HttpCollection,
    ) -> CollectionIterator:
        path, req, resp_schema = self._prepare_request(method, params, collection)
        resp = self._handle_req_with_middlewares(method, req, timeout, path)
        return self._prepare_collection_response(
            resp, resp_schema, collection.collection_parser
        )

    def _collection_request(
        self,
        method: HttpMethod,
        params: Union[Request, Dict[Any, Any]],
        timeout: HTTPTimeout,
    ) -> ResponseBox:
        path, req, resp_schema = self._prepare_request(
            method, params, self.routes.collection
        )
        resp = self._handle_req_with_middlewares(method, req, timeout, path)
        return self._prepare_response(resp, resp_schema, method, path)

    def _request(
        self,
        method: HttpMethod,
        params: Union[Request, Dict[Any, Any]],
        timeout: HTTPTimeout,
    ) -> ResponseBox:
        path, req, resp_schema = self._prepare_request(
            method, params, self.routes.resource
        )
        resp = self._handle_req_with_middlewares(method, req, timeout, path)
        return self._prepare_response(resp, resp_schema, method, path)

    def collection_head(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return self._collection_request(
            "HEAD", params, build_timeout(timeout or self.timeout)
        )

    def collection_get(
        self,
        params: Union[Optional[Request], Dict[Any, Any]] = None,
        timeout: Optional[ClientTimeout] = None,
    ) -> CollectionIterator:
        if not self.routes.collection:
            raise UnregisteredRouteException("GET", self.name, self.client_name)
        return self._yield_collection_request(
            "GET",
            params,
            build_timeout(timeout or self.timeout),
            self.routes.collection,
        )

    def collection_post(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return self._collection_request(
            "POST", params, build_timeout(timeout or self.timeout)
        )

    def collection_put(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return self._collection_request(
            "PUT", params, build_timeout(timeout or self.timeout)
        )

    def collection_patch(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return self._collection_request(
            "PATCH", params, build_timeout(timeout or self.timeout)
        )

    def collection_delete(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return self._collection_request(
            "DELETE", params, build_timeout(timeout or self.timeout)
        )

    def collection_options(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return self._collection_request(
            "OPTIONS", params, build_timeout(timeout or self.timeout)
        )

    def head(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return self._request("HEAD", params, build_timeout(timeout or self.timeout))

    def get(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        resp = self._request("GET", params, build_timeout(timeout or self.timeout))
        return resp

    def post(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return self._request("POST", params, build_timeout(timeout or self.timeout))

    def put(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return self._request("PUT", params, build_timeout(timeout or self.timeout))

    def patch(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return self._request("PATCH", params, build_timeout(timeout or self.timeout))

    def delete(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return self._request("DELETE", params, build_timeout(timeout or self.timeout))

    def options(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox:
        return self._request("OPTIONS", params, build_timeout(timeout or self.timeout))
