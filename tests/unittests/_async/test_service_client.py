from typing import cast

import pytest
from prometheus_client import CollectorRegistry

from blacksmith.domain.exceptions import (
    HTTPError,
    HTTPTimeoutError,
    NoContractException,
    UnregisteredResourceException,
    UnregisteredRouteException,
    WrongRequestTypeException,
)
from blacksmith.domain.model import (
    CollectionParser,
    HTTPRequest,
    HTTPResponse,
    HTTPTimeout,
    ResponseBox,
)
from blacksmith.domain.registry import ApiRoutes
from blacksmith.middleware._async.auth import AsyncHTTPAuthorization
from blacksmith.middleware._async.prometheus import AsyncPrometheusMetrics
from blacksmith.service._async.base import AsyncAbstractTransport
from blacksmith.service._async.client import AsyncClient, AsyncClientFactory
from blacksmith.typing import HttpMethod, Proxies
from tests.unittests.dummy_registry import (
    GetParam,
    GetResponse,
    PostParam,
    dummy_registry,
)


class FakeTransport(AsyncAbstractTransport):
    def __init__(self, resp: HTTPResponse) -> None:
        super().__init__()
        self.resp = resp

    async def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
        if self.resp.status_code >= 400:
            raise HTTPError(f"{self.resp.status_code} blah", request, self.resp)
        return self.resp


class FakeTimeoutTransport(AsyncAbstractTransport):
    async def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
        raise HTTPTimeoutError(f"ReadTimeout while calling {method} {request.url}")


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

    client = AsyncClient(
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
        str(ctx.value) == "Invalid type 'tests.unittests.dummy_registry.PostParam' "
        "for route 'GET' in resource 'dummies' in client 'api'"
    )


@pytest.mark.asyncio
async def test_client_timeout(static_sd):

    routes = ApiRoutes(
        "/dummies/{name}", {"GET": (GetParam, GetResponse)}, None, None, None
    )

    client = AsyncClient(
        "api",
        "http://dummies.v1",
        {"dummies": routes},
        transport=FakeTimeoutTransport(),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    with pytest.raises(HTTPTimeoutError) as exc:
        await client.dummies.get({"name": "barbie"})
    assert (
        str(exc.value)
        == "ReadTimeout while calling GET http://dummies.v1/dummies/barbie"
    )


@pytest.mark.asyncio
async def test_client_factory_config(static_sd):
    tp = FakeTimeoutTransport()
    client_factory = AsyncClientFactory(static_sd, tp, registry=dummy_registry)

    cli = await client_factory("api")

    assert cli.name == "api"
    assert cli.endpoint == "https://dummy.v1/"
    assert set(cli.resources.keys()) == {"dummies"}
    assert cli.transport == tp


def test_client_factory_configure_transport(static_sd):
    client_factory = AsyncClientFactory(static_sd, verify_certificate=False)
    assert client_factory.transport.verify_certificate is False


def test_client_factory_configure_proxies(static_sd):
    proxies: Proxies = {
        "http://": "http://localhost:8030",
        "https://": "http://localhost:8031",
    }
    client_factory = AsyncClientFactory(static_sd, proxies=proxies)
    assert client_factory.transport.proxies is proxies


@pytest.mark.asyncio
async def test_client_factory_add_middleware(static_sd, dummy_middleware):
    tp = FakeTimeoutTransport()
    auth = AsyncHTTPAuthorization("Bearer", "abc")
    prom = AsyncPrometheusMetrics(registry=CollectorRegistry())
    client_factory = (
        AsyncClientFactory(static_sd, tp, registry=dummy_registry)
        .add_middleware(prom)
        .add_middleware(auth)
    )
    assert client_factory.middlewares == [auth, prom]

    cli = await client_factory("api")
    assert cli.middlewares == [auth, prom]

    client_factory.add_middleware(dummy_middleware)
    assert client_factory.middlewares == [dummy_middleware, auth, prom]
    assert cli.middlewares == [auth, prom]
    assert cast(AsyncHTTPAuthorization, cli.middlewares[0]).headers == {
        "Authorization": "Bearer abc"
    }
    cast(AsyncHTTPAuthorization, client_factory.middlewares[0]).headers[
        "Authorization"
    ] = "Bearer xyz"
    assert cast(AsyncHTTPAuthorization, cli.middlewares[0]).headers == {
        "Authorization": "Bearer abc"
    }


@pytest.mark.asyncio
async def test_client_add_middleware(static_sd, dummy_middleware):
    tp = FakeTimeoutTransport()
    prom = AsyncPrometheusMetrics(registry=CollectorRegistry())
    auth = AsyncHTTPAuthorization("Bearer", "abc")
    client_factory = AsyncClientFactory(
        static_sd, tp, registry=dummy_registry
    ).add_middleware(prom)

    cli = await client_factory("api")
    assert cli.middlewares == [prom]
    cli.add_middleware(auth)

    assert cli.middlewares == [auth, prom]
    assert client_factory.middlewares == [prom]

    cli2 = (await client_factory("api")).add_middleware(dummy_middleware)
    assert cli2.middlewares == [dummy_middleware, prom]
    assert cli.middlewares == [auth, prom]
    assert client_factory.middlewares == [prom]


@pytest.mark.asyncio
async def test_client_factory_initialize_middlewares(
    echo_transport, static_sd, dummy_middleware
):
    client_factory = AsyncClientFactory(
        static_sd, echo_transport, registry=dummy_registry
    ).add_middleware(dummy_middleware)
    assert dummy_middleware.initialized == 0
    cli = await client_factory("api")
    await cli.dummies.get({"name": "foo"})
    assert dummy_middleware.initialized == 1
    cli = await client_factory("api")
    assert dummy_middleware.initialized == 1
