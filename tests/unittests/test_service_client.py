import pytest
from prometheus_client import CollectorRegistry

from blacksmith import PathInfoField, Request, Response
from blacksmith.domain.exceptions import (
    HTTPError,
    NoContractException,
    TimeoutError,
    UnregisteredResourceException,
    UnregisteredRouteException,
    WrongRequestTypeException,
)
from blacksmith.domain.model import (
    CollectionParser,
    HTTPRequest,
    HTTPResponse,
    HTTPTimeout,
    PostBodyField,
    ResponseBox,
)
from blacksmith.domain.registry import ApiRoutes, Registry
from blacksmith.middleware.auth import HTTPAuthorization
from blacksmith.middleware.prometheus import PrometheusMetrics
from blacksmith.service.base import AbstractTransport
from blacksmith.service.client import Client, ClientFactory
from blacksmith.typing import HttpMethod


class FakeTransport(AbstractTransport):
    def __init__(self, resp: HTTPResponse) -> None:
        super().__init__()
        self.resp = resp

    async def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
        if self.resp.status_code >= 400:
            raise HTTPError(f"{self.resp.status_code} blah", request, self.resp)
        return self.resp


class FakeTimeoutTransport(AbstractTransport):
    async def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
        raise TimeoutError(f"ReadTimeout while calling {method} {request.url}")


class GetParam(Request):
    name: str = PathInfoField(str)


class PostParam(Request):
    name: str = PostBodyField(str)
    age: int = PostBodyField(int)


class GetResponse(Response):
    name: str
    age: int


dummy_registry = Registry()
dummy_registry.register(
    "api",
    "dummies",
    "dummy",
    "v1",
    "/dummies/{name}",
    {"GET": (GetParam, GetResponse)},
)


@pytest.mark.asyncio
async def test_client(static_sd):

    resp = HTTPResponse(
        200,
        {},
        {
            "name": "Barbie",
            "age": 42,
            "hair_color": "blond",
        },
    )

    routes = ApiRoutes(
        "/dummies/{name}", {"GET": (GetParam, GetResponse)}, None, None, None
    )

    client = Client(
        "api",
        "https://dummies.v1",
        {"dummies": routes},
        transport=FakeTransport(resp),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )

    resp = await client.dummies.get({"name": "barbie"})
    assert isinstance(resp, ResponseBox)
    assert isinstance(resp.response, GetResponse)
    assert resp.response.dict() == {"name": "Barbie", "age": 42}
    assert resp.json == {
        "name": "Barbie",
        "age": 42,
        "hair_color": "blond",
    }

    resp = await client.dummies.get(GetParam(name="barbie"))
    assert isinstance(resp, ResponseBox)
    assert isinstance(resp.response, GetResponse)
    assert resp.response.dict() == {"name": "Barbie", "age": 42}

    with pytest.raises(UnregisteredResourceException) as ctx:
        client.daemon
    assert str(ctx.value) == "Unregistered resource 'daemon' in client 'api'"

    with pytest.raises(NoContractException) as ctx:
        await client.dummies.post({"name": "Barbie", "age": 42})

    assert (
        str(ctx.value)
        == "Unregistered route 'POST' in resource 'dummies' in client 'api'"
    )

    with pytest.raises(UnregisteredRouteException) as ctx:
        await client.dummies.collection_post({"name": "Barbie", "age": 42})
    assert (
        str(ctx.value)
        == "Unregistered route 'POST' in resource 'dummies' in client 'api'"
    )

    with pytest.raises(WrongRequestTypeException) as ctx:
        await client.dummies.get(PostParam(name="barbie", age=42))
    assert (
        str(ctx.value)
        == "Invalid type 'tests.unittests.test_service_client.PostParam' for route 'GET' "
        "in resource 'dummies' in client 'api'"
    )


@pytest.mark.asyncio
async def test_client_timeout(static_sd):

    resp = HTTPResponse(
        200,
        {},
        {
            "name": "timeout",
            "age": 42,
        },
    )

    routes = ApiRoutes(
        "/dummies/{name}", {"GET": (GetParam, GetResponse)}, None, None, None
    )

    client = Client(
        "api",
        "http://dummies.v1",
        {"dummies": routes},
        transport=FakeTimeoutTransport(),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    with pytest.raises(TimeoutError) as exc:
        await client.dummies.get({"name": "barbie"})
    assert (
        str(exc.value)
        == "ReadTimeout while calling GET http://dummies.v1/dummies/barbie"
    )


@pytest.mark.asyncio
async def test_client_factory(static_sd, dummy_middleware):
    tp = FakeTimeoutTransport()
    auth = HTTPAuthorization("Bearer", "abc")
    prom = PrometheusMetrics(registry=CollectorRegistry())
    client_factory = (
        ClientFactory(static_sd, tp, registry=dummy_registry)
        .add_middleware(prom)
        .add_middleware(auth)
    )
    assert client_factory.middlewares == [auth, prom]

    cli = await client_factory("api")

    assert cli.name == "api"
    assert cli.endpoint == "https://dummy.v1/"
    assert set(cli.resources.keys()) == {"dummies"}
    assert cli.transport == tp
    assert cli.middlewares == [auth, prom]

    client_factory.add_middleware(dummy_middleware)
    assert cli.middlewares == [dummy_middleware, auth, prom]


@pytest.mark.asyncio
async def test_client_factory_initialize_middlewares(
    echo_transport, static_sd, dummy_middleware
):
    client_factory = ClientFactory(
        static_sd, echo_transport, registry=dummy_registry
    ).add_middleware(dummy_middleware)
    assert dummy_middleware.initialized == 0
    cli = await client_factory("api")
    await cli.dummies.get({"name": "foo"})
    assert dummy_middleware.initialized == 1
    cli = await client_factory("api")
    assert dummy_middleware.initialized == 1
