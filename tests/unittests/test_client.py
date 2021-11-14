import pytest

from aioli import Request, PathInfoField, Response
from aioli.domain.exceptions import (
    NoContractException,
    UnregisteredResourceException,
    UnregisteredRouteException,
    WrongRequestTypeException,
)
from aioli.domain.model import (
    HTTPAuthorization,
    HTTPRequest,
    HTTPResponse,
    PostBodyField,
    HTTPUnauthenticated,
)
from aioli.domain.registry import ApiRoutes, Registry
from aioli.service.base import AbstractTransport
from aioli.typing import HttpMethod
from aioli.service.client import Client, ClientFactory


class FakeTransport(AbstractTransport):
    def __init__(self, resp: HTTPResponse) -> None:
        super().__init__()
        self.resp = resp

    async def request(self, method: HttpMethod, request: HTTPRequest) -> HTTPResponse:
        return self.resp


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
        {
            "name": "Barbie",
            "age": 42,
            "hair_color": "blond",
        },
    )

    routes = ApiRoutes("/dummies/{name}", {"GET": (GetParam, GetResponse)}, None, None)

    client = Client(
        "api",
        "https://dummies.v1",
        {"dummies": routes},
        transport=FakeTransport(resp),
        auth=HTTPUnauthenticated(),
    )

    resp = await client.dummies.get({"name": "barbie"})
    assert isinstance(resp, GetResponse)
    assert resp.dict() == {"name": "Barbie", "age": 42}

    resp = await client.dummies.get(GetParam(name="barbie"))
    assert isinstance(resp, GetResponse)
    assert resp.dict() == {"name": "Barbie", "age": 42}

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
        str(ctx.value) == "Invalid type 'tests.unittests.test_client.PostParam' for route 'GET' "
        "in resource 'dummies' in client 'api'"
    )


@pytest.mark.asyncio
async def test_client_factory(static_sd):
    resp = HTTPResponse(200, {})
    tp = FakeTransport(resp)
    auth = HTTPAuthorization("Bearer", "abc")
    client = ClientFactory(static_sd, auth, tp, registry=dummy_registry)
    cli = await client("api")

    assert cli.name == "api"
    assert cli.endpoint == "https://dummy.v1/"
    assert set(cli.resources.keys()) == {"dummies"}
    assert cli.transport == tp
    assert cli.auth == auth
