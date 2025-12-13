from typing import (
    Any,
    Generic,
    cast,
)

from result import Err, Ok, Result

from blacksmith.domain.error import AbstractErrorParser, TError_co
from blacksmith.domain.exceptions import (
    HTTPError,
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
from blacksmith.domain.model.params import (
    AbstractCollectionParser,
    TCollectionResponse,
    TResponse,
)
from blacksmith.domain.registry import ApiRoutes, HttpCollection, HttpResource
from blacksmith.domain.typing import SyncMiddleware
from blacksmith.middleware._sync.base import SyncHTTPMiddleware
from blacksmith.service.http_body_serializer import serialize_request
from blacksmith.shared_utils.introspection import (
    build_pydantic_union,
    is_instance_with_union,
)
from blacksmith.typing import ClientName, HTTPMethod, Path, ResourceName, Url

from .base import SyncAbstractTransport

ClientTimeout = HTTPTimeout | float | tuple[float, float]
HTTPAuthentication = SyncHTTPMiddleware


def build_timeout(timeout: ClientTimeout) -> HTTPTimeout:
    """Build the timeout from the convenient timeout."""
    if isinstance(timeout, float):
        timeout = HTTPTimeout(timeout)
    elif isinstance(timeout, tuple):
        timeout = HTTPTimeout(*timeout)
    return timeout


class SyncRouteProxy(Generic[TCollectionResponse, TResponse, TError_co]):
    """Proxy from resource to its associate routes."""

    client_name: ClientName
    name: ResourceName
    endpoint: Url
    routes: ApiRoutes
    transport: SyncAbstractTransport
    timeout: HTTPTimeout
    collection_parser: type[AbstractCollectionParser]
    error_parser: AbstractErrorParser[TError_co]
    middlewares: list[SyncHTTPMiddleware]

    def __init__(
        self,
        client_name: ClientName,
        name: ResourceName,
        endpoint: Url,
        routes: ApiRoutes,
        transport: SyncAbstractTransport,
        timeout: HTTPTimeout,
        collection_parser: type[AbstractCollectionParser],
        error_parser: AbstractErrorParser[TError_co],
        middlewares: list[SyncHTTPMiddleware],
    ) -> None:
        self.client_name = client_name
        self.name = name
        self.endpoint = endpoint
        self.routes = routes
        self.transport = transport
        self.timeout = timeout
        self.collection_parser = collection_parser
        self.error_parser = error_parser
        self.middlewares = middlewares

    def _prepare_request(
        self,
        method: HTTPMethod,
        params: Request | dict[Any, Any] | None,
        resource: HttpResource | None,
    ) -> tuple[Path, HTTPRequest, type[Response]]:
        if resource is None:
            raise UnregisteredRouteException(method, self.name, self.client_name)
        if resource.contract is None or method not in resource.contract:
            raise NoContractException(method, self.name, self.client_name)

        param_schema, return_schema = resource.contract[method]
        build_params: Request
        if isinstance(params, dict):
            build_params = cast(Request, build_pydantic_union(param_schema, params))
        elif params is None:
            build_params = param_schema()
        elif not is_instance_with_union(params, param_schema):
            raise WrongRequestTypeException(
                params.__class__,  # type: ignore
                method,
                self.name,
                self.client_name,
            )
        else:
            build_params = params
        req = serialize_request(method, self.endpoint + resource.path, build_params)
        return (resource.path, req, return_schema)

    def _prepare_response(
        self,
        result: Result[HTTPResponse, HTTPError],
        response_schema: type[Response],
        method: HTTPMethod,
        path: Path,
    ) -> ResponseBox[TResponse, TError_co]:
        return ResponseBox[TResponse, TError_co](
            result,
            cast(type[TResponse], response_schema),
            method,
            path,
            self.name,
            self.client_name,
            self.error_parser,
        )

    def _prepare_collection_response(
        self,
        result: Result[HTTPResponse, HTTPError],
        response_schema: type[Response],
        collection_parser: type[AbstractCollectionParser] | None,
    ) -> Result[CollectionIterator[TCollectionResponse], TError_co]:
        if result.is_err():
            return Err(self.error_parser(result.unwrap_err()))
        else:
            return Ok(
                CollectionIterator(
                    result.unwrap(),
                    response_schema,
                    collection_parser or self.collection_parser,
                )
            )

    def _handle_req_with_middlewares(
        self, req: HTTPRequest, timeout: HTTPTimeout, path: Path
    ) -> Result[HTTPResponse, HTTPError]:
        next: SyncMiddleware = self.transport
        for middleware in self.middlewares:
            next = middleware(next)

        try:
            resp = next(req, self.client_name, path, timeout)
        except HTTPError as exc:
            return Err(exc)
        return Ok(resp)

    def _yield_collection_request(
        self,
        method: HTTPMethod,
        params: Request | None | dict[Any, Any],
        timeout: HTTPTimeout,
        collection: HttpCollection,
    ) -> Result[CollectionIterator[TCollectionResponse], TError_co]:
        path, req, resp_schema = self._prepare_request(method, params, collection)
        resp = self._handle_req_with_middlewares(req, timeout, path)
        return self._prepare_collection_response(
            resp, resp_schema, collection.collection_parser
        )

    def _collection_request(
        self,
        method: HTTPMethod,
        params: Request | dict[Any, Any],
        timeout: HTTPTimeout,
    ) -> ResponseBox[TResponse, TError_co]:
        path, req, resp_schema = self._prepare_request(
            method, params, self.routes.collection
        )
        resp = self._handle_req_with_middlewares(req, timeout, path)
        return self._prepare_response(resp, resp_schema, method, path)

    def _request(
        self,
        method: HTTPMethod,
        params: Request | dict[Any, Any],
        timeout: HTTPTimeout,
    ) -> ResponseBox[TResponse, TError_co]:
        path, req, resp_schema = self._prepare_request(
            method, params, self.routes.resource
        )
        resp = self._handle_req_with_middlewares(req, timeout, path)
        return self._prepare_response(resp, resp_schema, method, path)

    def collection_head(
        self,
        params: Request | dict[Any, Any],
        timeout: ClientTimeout | None = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``HEAD`` query on the collection_path.
        """
        return self._collection_request(
            "HEAD", params, build_timeout(timeout or self.timeout)
        )

    def collection_get(
        self,
        params: Request | None | dict[Any, Any] = None,
        timeout: ClientTimeout | None = None,
    ) -> Result[CollectionIterator[TCollectionResponse], TError_co]:
        """
        Retrieve a collection of resources.

        It perform an http ``GET`` query on the collection_path.

        The collection is return in as an iterator, and models ares validated one
        by one using the `TCollectionResponse` schema which descrine one item
        of the collection.

        .. important::
            This method is the only method that behave as an iterator.
            You can update the way collection are deserialize for a whole client,
            by passing a :class:`blacksmith.AbstractCollectionParser` on the
            :class:`blacksmith.AsyncClientFactory` (
            or :class:`blacksmith.SyncClientFactory` for the synchronous version).
        """
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
        params: Request | dict[Any, Any],
        timeout: ClientTimeout | None = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``POST`` query on the collection_path.
        """
        return self._collection_request(
            "POST", params, build_timeout(timeout or self.timeout)
        )

    def collection_put(
        self,
        params: Request | dict[Any, Any],
        timeout: ClientTimeout | None = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``PUT`` query on the collection_path.
        """
        return self._collection_request(
            "PUT", params, build_timeout(timeout or self.timeout)
        )

    def collection_patch(
        self,
        params: Request | dict[Any, Any],
        timeout: ClientTimeout | None = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``PATCH`` query on the collection_path.
        """
        return self._collection_request(
            "PATCH", params, build_timeout(timeout or self.timeout)
        )

    def collection_delete(
        self,
        params: Request | dict[Any, Any],
        timeout: ClientTimeout | None = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``DELETE`` query on the collection_path.
        """
        return self._collection_request(
            "DELETE", params, build_timeout(timeout or self.timeout)
        )

    def collection_options(
        self,
        params: Request | dict[Any, Any],
        timeout: ClientTimeout | None = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``OPTIONS`` query on the collection_path.
        """
        return self._collection_request(
            "OPTIONS", params, build_timeout(timeout or self.timeout)
        )

    def head(
        self,
        params: Request | dict[Any, Any],
        timeout: ClientTimeout | None = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``HEAD`` query on the path.
        """
        return self._request("HEAD", params, build_timeout(timeout or self.timeout))

    def get(
        self,
        params: Request | dict[Any, Any],
        timeout: ClientTimeout | None = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``GET`` query on the path.
        """
        resp = self._request("GET", params, build_timeout(timeout or self.timeout))
        return resp

    def post(
        self,
        params: Request | dict[Any, Any],
        timeout: ClientTimeout | None = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``POST`` query on the path.
        """
        return self._request("POST", params, build_timeout(timeout or self.timeout))

    def put(
        self,
        params: Request | dict[Any, Any],
        timeout: ClientTimeout | None = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``PUT`` query on the path.
        """
        return self._request("PUT", params, build_timeout(timeout or self.timeout))

    def patch(
        self,
        params: Request | dict[Any, Any],
        timeout: ClientTimeout | None = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``PATCH`` query on the path.
        """
        return self._request("PATCH", params, build_timeout(timeout or self.timeout))

    def delete(
        self,
        params: Request | dict[Any, Any],
        timeout: ClientTimeout | None = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``DELETE`` query on the path.
        """
        return self._request("DELETE", params, build_timeout(timeout or self.timeout))

    def options(
        self,
        params: Request | dict[Any, Any],
        timeout: ClientTimeout | None = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``OPTIONS`` query on the path.
        """
        return self._request("OPTIONS", params, build_timeout(timeout or self.timeout))
