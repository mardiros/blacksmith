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
from aioli.service.client import Client, ClientFactory, RouteProxy


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
        str(ctx.value)
        == "Invalid type 'tests.unittests.test_client.PostParam' for route 'GET' "
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


@pytest.mark.asyncio
async def test_route_proxy_prepare_unregistered_method_resource():
    resp = HTTPResponse(200, "")
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            "/",
            {},
            None,
            None,
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    with pytest.raises(NoContractException) as exc:
        resp = proxy._prepare_request(
            "GET", {}, proxy.routes.resource, HTTPUnauthenticated()
        )
    assert (
        str(exc.value)
        == "Unregistered route 'GET' in resource 'dummies' in client 'dummy'"
    )


@pytest.mark.asyncio
async def test_route_proxy_prepare_unregistered_method_collection():
    resp = HTTPResponse(200, "")
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            "/",
            {},
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    with pytest.raises(NoContractException) as exc:
        resp = proxy._prepare_request(
            "GET", {}, proxy.routes.collection, HTTPUnauthenticated()
        )
    assert (
        str(exc.value)
        == "Unregistered route 'GET' in resource 'dummies' in client 'dummy'"
    )


@pytest.mark.asyncio
async def test_route_proxy_prepare_unregistered_resource():
    resp = HTTPResponse(200, "")
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            "/",
            {},
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    with pytest.raises(UnregisteredRouteException) as exc:
        resp = proxy._prepare_request(
            "GET", {}, proxy.routes.resource, HTTPUnauthenticated()
        )
    assert (
        str(exc.value)
        == "Unregistered route 'GET' in resource 'dummies' in client 'dummy'"
    )


@pytest.mark.asyncio
async def test_route_proxy_prepare_unregistered_collection():
    resp = HTTPResponse(200, "")
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            "/",
            {},
            None,
            None,
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    with pytest.raises(UnregisteredRouteException) as exc:
        resp = proxy._prepare_request(
            "GET", {}, proxy.routes.collection, HTTPUnauthenticated()
        )
    assert (
        str(exc.value)
        == "Unregistered route 'GET' in resource 'dummies' in client 'dummy'"
    )


@pytest.mark.asyncio
async def test_route_proxy_collection_head():
    resp = HTTPResponse(200, "")
    tp = FakeTransport(resp)
    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"HEAD": (Request, None)},
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    resp = await proxy.collection_head({"name": "baby"})
    assert resp == ""


@pytest.mark.asyncio
async def test_route_proxy_collection_get():
    resp = HTTPResponse(200, [{"name": "alice"}, {"name": "bob"}])
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"GET": (Request, None)},
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    resp = await proxy.collection_get()
    resp = list(resp)
    assert resp == [{"name": "alice"}, {"name": "bob"}]


@pytest.mark.asyncio
async def test_route_proxy_collection_post():
    resp = HTTPResponse(202, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"POST": (Request, None)},
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    resp = await proxy.collection_post({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_collection_put():
    resp = HTTPResponse(202, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"PUT": (Request, None)},
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    resp = await proxy.collection_put({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_collection_patch():
    resp = HTTPResponse(202, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"PATCH": (Request, None)},
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    resp = await proxy.collection_patch({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_collection_delete():
    resp = HTTPResponse(202, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"DELETE": (Request, None)},
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    resp = await proxy.collection_delete({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_collection_options():
    resp = HTTPResponse(202, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"OPTIONS": (Request, None)},
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    resp = await proxy.collection_options({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_head():
    resp = HTTPResponse(200, "")
    tp = FakeTransport(resp)
    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"HEAD": (Request, None)},
            collection_contract=None,
            collection_path=None,
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    resp = await proxy.head({"name": "baby"})
    assert resp == ""


@pytest.mark.asyncio
async def test_route_proxy_get():
    resp = HTTPResponse(200, [{"name": "alice"}, {"name": "bob"}])
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"GET": (Request, None)},
            collection_contract=None,
            collection_path=None,
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    resp = await proxy.get({})
    assert resp == [{"name": "alice"}, {"name": "bob"}]


@pytest.mark.asyncio
async def test_route_proxy_post():
    resp = HTTPResponse(202, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"POST": (Request, None)},
            collection_contract=None,
            collection_path=None,
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    resp = await proxy.post({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_put():
    resp = HTTPResponse(202, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"PUT": (Request, None)},
            collection_contract=None,
            collection_path=None,
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    resp = await proxy.put({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_patch():
    resp = HTTPResponse(202, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"PATCH": (Request, None)},
            collection_contract=None,
            collection_path=None,
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    resp = await proxy.patch({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_delete():
    resp = HTTPResponse(202, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"DELETE": (Request, None)},
            collection_contract=None,
            collection_path=None,
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    resp = await proxy.delete({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_options():
    resp = HTTPResponse(202, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = RouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"OPTIONS": (Request, None)},
            collection_contract=None,
            collection_path=None,
        ),
        tp,
        HTTPAuthorization("Bearer", "abc"),
    )
    resp = await proxy.options({})
    assert resp == {"detail": "accepted"}
