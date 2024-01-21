from typing import Any, Dict, Generic, List, Mapping, Optional, Tuple, Type, Union

try:
    from types import UnionType  # type: ignore
except ImportError:  # coverage: ignore
    # python 3.7 compat
    UnionType = Union  # type: ignore

from pydantic import ValidationError
from result import Err, Ok, Result
from typing_extensions import get_origin

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
from blacksmith.domain.typing import AsyncMiddleware
from blacksmith.middleware._async.base import AsyncHTTPMiddleware
from blacksmith.service.http_body_serializer import serialize_request
from blacksmith.typing import ClientName, HTTPMethod, Path, ResourceName, Url

from .base import AsyncAbstractTransport

ClientTimeout = Union[HTTPTimeout, float, Tuple[float, float]]
HTTPAuthentication = AsyncHTTPMiddleware


def build_timeout(timeout: ClientTimeout) -> HTTPTimeout:
    """Build the timeout from the convenient timeout."""
    if isinstance(timeout, float):
        timeout = HTTPTimeout(timeout)
    elif isinstance(timeout, tuple):
        timeout = HTTPTimeout(*timeout)
    return timeout


def is_union(typ: Type[Any]) -> bool:
    type_origin = get_origin(typ)
    if type_origin:
        if type_origin is Union:  # Union[T, U] or even Optional[T]
            return True

        if type_origin is UnionType:  # T | U
            return True
    return False


def is_instance_with_union(val: Any, typ: Type[Any]) -> bool:
    # isinstance does not support union type in old interpreter,
    if is_union(typ):
        r = [isinstance(val, t) for t in typ.__args__]  # type: ignore
        return any(r)
    return isinstance(val, typ)


def build_request(typ: Type[Any], params: Mapping[str, Any]) -> Request:
    if is_union(typ):
        err: Optional[Exception] = None
        for t in typ.__args__:  # type: ignore
            try:
                return build_request(t, params)  # type: ignore
            except ValidationError as e:
                err = e
        if err:
            raise err
    return typ(**params)


class AsyncRouteProxy(Generic[TCollectionResponse, TResponse, TError_co]):
    """Proxy from resource to its associate routes."""

    client_name: ClientName
    name: ResourceName
    endpoint: Url
    routes: ApiRoutes
    transport: AsyncAbstractTransport
    timeout: HTTPTimeout
    collection_parser: Type[AbstractCollectionParser]
    error_parser: AbstractErrorParser[TError_co]
    middlewares: List[AsyncHTTPMiddleware]

    def __init__(
        self,
        client_name: ClientName,
        name: ResourceName,
        endpoint: Url,
        routes: ApiRoutes,
        transport: AsyncAbstractTransport,
        timeout: HTTPTimeout,
        collection_parser: Type[AbstractCollectionParser],
        error_parser: AbstractErrorParser[TError_co],
        middlewares: List[AsyncHTTPMiddleware],
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
        params: Union[Optional[Request], Dict[Any, Any]],
        resource: Optional[HttpResource],
    ) -> Tuple[Path, HTTPRequest, Optional[Type[Response]]]:
        if resource is None:
            raise UnregisteredRouteException(method, self.name, self.client_name)
        if resource.contract is None or method not in resource.contract:
            raise NoContractException(method, self.name, self.client_name)

        param_schema, return_schema = resource.contract[method]
        build_params: Request
        if isinstance(params, dict):
            build_params = build_request(param_schema, params)
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
        response_schema: Optional[Type[Response]],
        method: HTTPMethod,
        path: Path,
    ) -> ResponseBox[TResponse, TError_co]:
        return ResponseBox[TResponse, TError_co](
            result,
            response_schema,
            method,
            path,
            self.name,
            self.client_name,
            self.error_parser,
        )

    def _prepare_collection_response(
        self,
        result: Result[HTTPResponse, HTTPError],
        response_schema: Optional[Type[Response]],
        collection_parser: Optional[Type[AbstractCollectionParser]],
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

    async def _handle_req_with_middlewares(
        self, req: HTTPRequest, timeout: HTTPTimeout, path: Path
    ) -> Result[HTTPResponse, HTTPError]:
        next: AsyncMiddleware = self.transport
        for middleware in self.middlewares:
            next = middleware(next)

        try:
            resp = await next(req, self.client_name, path, timeout)
        except HTTPError as exc:
            return Err(exc)
        return Ok(resp)

    async def _yield_collection_request(
        self,
        method: HTTPMethod,
        params: Union[Optional[Request], Dict[Any, Any]],
        timeout: HTTPTimeout,
        collection: HttpCollection,
    ) -> Result[CollectionIterator[TCollectionResponse], TError_co]:
        path, req, resp_schema = self._prepare_request(method, params, collection)
        resp = await self._handle_req_with_middlewares(req, timeout, path)
        return self._prepare_collection_response(
            resp, resp_schema, collection.collection_parser
        )

    async def _collection_request(
        self,
        method: HTTPMethod,
        params: Union[Request, Dict[Any, Any]],
        timeout: HTTPTimeout,
    ) -> ResponseBox[TResponse, TError_co]:
        path, req, resp_schema = self._prepare_request(
            method, params, self.routes.collection
        )
        resp = await self._handle_req_with_middlewares(req, timeout, path)
        return self._prepare_response(resp, resp_schema, method, path)

    async def _request(
        self,
        method: HTTPMethod,
        params: Union[Request, Dict[Any, Any]],
        timeout: HTTPTimeout,
    ) -> ResponseBox[TResponse, TError_co]:
        path, req, resp_schema = self._prepare_request(
            method, params, self.routes.resource
        )
        resp = await self._handle_req_with_middlewares(req, timeout, path)
        return self._prepare_response(resp, resp_schema, method, path)

    async def collection_head(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``HEAD`` query on the collection_path.
        """
        return await self._collection_request(
            "HEAD", params, build_timeout(timeout or self.timeout)
        )

    async def collection_get(
        self,
        params: Union[Optional[Request], Dict[Any, Any]] = None,
        timeout: Optional[ClientTimeout] = None,
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
        return await self._yield_collection_request(
            "GET",
            params,
            build_timeout(timeout or self.timeout),
            self.routes.collection,
        )

    async def collection_post(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``POST`` query on the collection_path.
        """
        return await self._collection_request(
            "POST", params, build_timeout(timeout or self.timeout)
        )

    async def collection_put(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``PUT`` query on the collection_path.
        """
        return await self._collection_request(
            "PUT", params, build_timeout(timeout or self.timeout)
        )

    async def collection_patch(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``PATCH`` query on the collection_path.
        """
        return await self._collection_request(
            "PATCH", params, build_timeout(timeout or self.timeout)
        )

    async def collection_delete(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``DELETE`` query on the collection_path.
        """
        return await self._collection_request(
            "DELETE", params, build_timeout(timeout or self.timeout)
        )

    async def collection_options(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``OPTIONS`` query on the collection_path.
        """
        return await self._collection_request(
            "OPTIONS", params, build_timeout(timeout or self.timeout)
        )

    async def head(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``HEAD`` query on the path.
        """
        return await self._request(
            "HEAD", params, build_timeout(timeout or self.timeout)
        )

    async def get(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``GET`` query on the path.
        """
        resp = await self._request(
            "GET", params, build_timeout(timeout or self.timeout)
        )
        return resp

    async def post(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``POST`` query on the path.
        """
        return await self._request(
            "POST", params, build_timeout(timeout or self.timeout)
        )

    async def put(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``PUT`` query on the path.
        """
        return await self._request(
            "PUT", params, build_timeout(timeout or self.timeout)
        )

    async def patch(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``PATCH`` query on the path.
        """
        return await self._request(
            "PATCH", params, build_timeout(timeout or self.timeout)
        )

    async def delete(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``DELETE`` query on the path.
        """
        return await self._request(
            "DELETE", params, build_timeout(timeout or self.timeout)
        )

    async def options(
        self,
        params: Union[Request, Dict[Any, Any]],
        timeout: Optional[ClientTimeout] = None,
    ) -> ResponseBox[TResponse, TError_co]:
        """
        Use to perform an http ``OPTIONS`` query on the path.
        """
        return await self._request(
            "OPTIONS", params, build_timeout(timeout or self.timeout)
        )
