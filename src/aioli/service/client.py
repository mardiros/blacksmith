from typing import Any, Dict, Generator, Optional, Tuple, Type, Union

from aioli.service.adapters.httpx import HttpxTransport

from ..domain.exceptions import (
    NoContractException,
    UnregisteredResourceException,
    UnregisteredRouteException,
    WrongRequestTypeException,
)
from ..domain.model import (
    HTTPAuthentication,
    HTTPRequest,
    HTTPResponse,
    HTTPUnauthenticated,
    Request,
    Response,
)
from ..domain.registry import (
    ApiRoutes,
    HttpResource,
    Registry,
    Resources,
    registry as default_registry,
)
from ..sd.base import AbtractServiceDiscovery
from ..typing import ClientName, HttpMethod, ResourceName, Url
from .base import AbstractTransport


ResourceResponse = Optional[Union[Response, Dict[Any, Any]]]


class RouteProxy:
    """Proxy from resource to its associate routes."""

    client_name: ClientName
    name: ResourceName
    endpoint: Url
    routes: ApiRoutes
    transport: AbstractTransport
    auth: HTTPAuthentication

    def __init__(
        self,
        client_name: ClientName,
        name: ResourceName,
        endpoint: Url,
        routes: ApiRoutes,
        transport: AbstractTransport,
        auth: HTTPAuthentication,
    ) -> None:
        self.client_name = client_name
        self.name = name
        self.endpoint = endpoint
        self.routes = routes
        self.transport = transport
        self.auth = auth

    def _prepare_request(
        self,
        method: HttpMethod,
        params: Union[Optional[Request], Dict[Any, Any]],
        resource: Optional[HttpResource],
        auth: HTTPAuthentication,
    ) -> Tuple[HTTPRequest, Optional[Type[Response]]]:
        if resource is None:
            raise UnregisteredRouteException(method, self.name, self.client_name)
        if resource.contract is None or method not in resource.contract:
            raise NoContractException(method, self.name, self.client_name)

        # XXX Assume that the index error are not raised du to strong typing
        param_schema = resource.contract[method][0]
        return_schema = resource.contract[method][1]
        if isinstance(params, dict):
            params = param_schema(**params)
        elif params is None:
            params = param_schema()
        elif not isinstance(params, param_schema):
            raise WrongRequestTypeException(
                params.__class__, method, self.name, self.client_name
            )
        return (
            params.to_http_request(self.endpoint + resource.path).merge_authentication(
                auth
            ),
            return_schema,
        )

    def _prepare_response(
        self, response: HTTPResponse, response_schema: Optional[Type[Response]]
    ) -> ResourceResponse:
        if response_schema:
            resp = response_schema.from_http_response(response)
        else:
            resp = response.json
        return resp

    def _prepare_collection_response(
        self, response: HTTPResponse, response_schema: Optional[Type[Response]]
    ) -> Generator[ResourceResponse, None, None]:
        if response_schema:
            resp = response_schema.from_http_collection(response)
        else:
            resp = response.json or []
        for ret in resp:
            yield ret

    async def _yield_collection_request(
        self,
        method: HttpMethod,
        params: Union[Optional[Request], Dict[Any, Any]],
        auth: HTTPAuthentication,
    ) -> Generator[ResourceResponse, None, None]:
        req, resp_schema = self._prepare_request(
            method, params, self.routes.collection, auth
        )
        resp = await self.transport.request(method, req)
        return self._prepare_collection_response(resp, resp_schema)

    async def _collection_request(
        self,
        method: HttpMethod,
        params: Union[Request, Dict[Any, Any]],
        auth: HTTPAuthentication,
    ) -> ResourceResponse:
        req, resp_schema = self._prepare_request(
            method, params, self.routes.collection, auth
        )
        resp = await self.transport.request(method, req)
        return self._prepare_response(resp, resp_schema)

    async def _request(
        self,
        method: HttpMethod,
        params: Union[Request, Dict[Any, Any]],
        auth: HTTPAuthentication,
    ) -> ResourceResponse:
        req, resp_schema = self._prepare_request(
            method, params, self.routes.resource, auth
        )
        resp = await self.transport.request(method, req)
        return self._prepare_response(resp, resp_schema)

    async def collection_get(
        self,
        params: Union[Optional[Request], Dict[Any, Any]] = None,
        auth: Optional[HTTPAuthentication] = None,
    ) -> Generator[ResourceResponse, None, None]:
        return await self._yield_collection_request(
            "GET",
            params,
            auth or self.auth,
        )

    async def collection_post(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
    ) -> ResourceResponse:
        return await self._collection_request("POST", params, auth or self.auth)

    async def collection_put(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
    ) -> ResourceResponse:
        return await self._request("PUT", params, auth or self.auth)

    async def collection_patch(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
    ) -> ResourceResponse:
        return await self._request("PATCH", params, auth or self.auth)

    async def collection_delete(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
    ) -> ResourceResponse:
        return await self._request("DELETE", params, auth or self.auth)

    async def collection_options(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
    ) -> ResourceResponse:
        return await self._request("OPTIONS", params, auth or self.auth)

    async def get(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
    ) -> ResourceResponse:
        return await self._request("GET", params, auth or self.auth)

    async def post(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
    ) -> ResourceResponse:
        return await self._request("POST", params, auth or self.auth)

    async def put(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
    ) -> ResourceResponse:
        return await self._request("PUT", params, auth or self.auth)

    async def patch(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
    ) -> ResourceResponse:
        return await self._request("PATCH", params, auth or self.auth)

    async def delete(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
    ) -> ResourceResponse:
        return await self._request("DELETE", params, auth or self.auth)

    async def options(
        self,
        params: Union[Request, Dict[Any, Any]],
        auth: Optional[HTTPAuthentication] = None,
    ) -> ResourceResponse:
        return await self._request("OPTIONS", params, auth or self.auth)


class Client:
    """Client representatio for the client name."""

    name: ClientName
    endpoint: Url
    resources: Resources
    transport: AbstractTransport
    auth: HTTPAuthentication

    def __init__(
        self,
        name: ClientName,
        endpoint: Url,
        resources: Resources,
        transport: AbstractTransport,
        auth: HTTPAuthentication,
    ) -> None:
        self.name = name
        self.endpoint = endpoint
        self.resources = resources
        self.transport = transport
        self.auth = auth

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
    """

    sd: AbtractServiceDiscovery
    registry: Registry
    transport: AbstractTransport
    auth: HTTPAuthentication

    def __init__(
        self,
        sd: AbtractServiceDiscovery,
        auth: HTTPAuthentication = HTTPUnauthenticated(),
        transport: AbstractTransport = None,
        registry: Registry = default_registry,
    ) -> None:
        self.sd = sd
        self.registry = registry
        self.transport = transport or HttpxTransport()
        self.auth = auth

    async def __call__(
        self, client_name: ClientName, auth: Optional[HTTPAuthentication] = None
    ):
        srv, resources = self.registry.get_service(client_name)
        endpoint = await self.sd.get_endpoint(srv[0], srv[1])
        return Client(
            client_name, endpoint, resources, self.transport, auth or self.auth
        )
