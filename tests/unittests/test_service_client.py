import pytest

from aioli import PathInfoField, Request, Response
from aioli.domain.exceptions import (
    HTTPError,
    NoContractException,
    TimeoutError,
    UnregisteredResourceException,
    UnregisteredRouteException,
    WrongRequestTypeException,
)
from aioli.domain.model import (
    CollectionParser,
    HTTPRequest,
    HTTPResponse,
    HTTPTimeout,
    PostBodyField,
    ResponseBox,
)
from aioli.domain.registry import ApiRoutes, Registry
from aioli.middleware.auth import HTTPAuthorization, HTTPUnauthenticated
from aioli.monitoring import SinkholeMetrics
from aioli.service.base import AbstractTransport
from aioli.service.client import Client, ClientFactory
from aioli.typing import HttpMethod


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
        auth=HTTPUnauthenticated(),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        metrics=SinkholeMetrics(),
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
        auth=HTTPUnauthenticated(),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        metrics=SinkholeMetrics(),
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
    client = ClientFactory(static_sd, auth, tp, registry=dummy_registry)
    assert client.middlewares == []

    cli = await client("api")

    assert cli.name == "api"
    assert cli.endpoint == "https://dummy.v1/"
    assert set(cli.resources.keys()) == {"dummies"}
    assert cli.transport == tp
    assert cli.auth == auth
    assert cli.middlewares == []

    client.add_middleware(dummy_middleware)
    assert cli.middlewares == [dummy_middleware]
