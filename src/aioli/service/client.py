from typing import Any, Dict, Optional, Tuple, Type, Union

from aioli.service.adapters.httpx import HttpxTransport

from ..domain.exceptions import (
    NoContractException,
    UnregisteredResourceException,
    UnregisteredRouteException,
    WrongParamsTypeException,
)
from ..domain.model import HTTPRequest, HTTPResponse, Params, Response
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

    def __init__(
        self,
        client_name: ClientName,
        name: ResourceName,
        endpoint: Url,
        routes: ApiRoutes,
        transport: AbstractTransport,
    ) -> None:
        self.client_name = client_name
        self.name = name
        self.endpoint = endpoint
        self.routes = routes
        self.transport = transport

    def _prepare_request(
        self,
        method: HttpMethod,
        params: Union[Params, Dict[Any, Any]],
        resource: Optional[HttpResource],
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
        elif not isinstance(params, param_schema):
            raise WrongParamsTypeException(
                params.__class__, method, self.name, self.client_name
            )
        return (
            params.to_http_request(self.endpoint + resource.path),
            return_schema,
        )

    def _prepare_response(
        self, response: HTTPResponse, response_schema: Optional[Type[Response]]
    ):
        if response_schema:
            resp = response_schema.from_http_response(response)
        else:
            resp = response.json
        return resp

    async def collection_request(
        self, method: HttpMethod, params: Union[Params, Dict[Any, Any]]
    ) -> ResourceResponse:
        req, resp_schema = self._prepare_request(method, params, self.routes.collection)
        resp = await self.transport.request(method, req)
        return self._prepare_response(resp, resp_schema)

    async def request(
        self, method: HttpMethod, params: Union[Params, Dict[Any, Any]]
    ) -> ResourceResponse:
        req, resp_schema = self._prepare_request(method, params, self.routes.resource)
        resp = await self.transport.request(method, req)
        return self._prepare_response(resp, resp_schema)

    """
    async def collection_get(self, params: Params) -> Generator[ResourceResponse, None, None]:
        pass
    """

    async def collection_post(self, params: Params) -> ResourceResponse:
        return await self.collection_request("POST", params)

    async def collection_put(self, params: Params) -> ResourceResponse:
        return await self.collection_request("PUT", params)

    async def collection_patch(self, params: Params) -> ResourceResponse:
        return await self.collection_request("PATCH", params)

    async def collection_delete(self, params: Params) -> ResourceResponse:
        return await self.collection_request("DELETE", params)

    async def collection_options(self, params: Params) -> ResourceResponse:
        return await self.collection_request("OPTIONS", params)

    async def get(self, params: Union[Params, Dict[Any, Any]]) -> ResourceResponse:
        return await self.request("GET", params)

    async def post(self, params: Params) -> ResourceResponse:
        return await self.request("POST", params)

    async def put(self, params: Params) -> ResourceResponse:
        return await self.request("PUT", params)

    async def patch(self, params: Params) -> ResourceResponse:
        return await self.request("PATCH", params)

    async def delete(self, params: Params) -> ResourceResponse:
        return await self.request("DELETE", params)

    async def options(self, params: Params) -> ResourceResponse:
        return await self.request("OPTIONS", params)


class Client:
    """Client representatio for the client name."""
    name: ClientName
    endpoint: Url
    resources: Resources
    transport: AbstractTransport

    def __init__(
        self,
        name: ClientName,
        endpoint: Url,
        resources: Resources,
        transport: AbstractTransport,
    ) -> None:
        self.name = name
        self.endpoint = endpoint
        self.resources = resources
        self.transport = transport

    def __getattr__(self, name: ResourceName) -> RouteProxy:
        """
        The client has attributes that are the registered resource.
        
        The resource are registered using the :func:`aioli.register` function.
        """
        try:
            return RouteProxy(
                self.name, name, self.endpoint, self.resources[name], self.transport
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

    def __init__(
        self,
        sd: AbtractServiceDiscovery,
        transport: AbstractTransport = None,
        registry: Registry = default_registry,
    ) -> None:
        self.sd = sd
        self.registry = registry
        self.transport = transport or HttpxTransport()

    async def __call__(self, client_name: ClientName):
        srv, resources = self.registry.get_service(client_name)
        endpoint = await self.sd.get_endpoint(srv[0], srv[1])
        return Client(client_name, endpoint, resources, self.transport)
