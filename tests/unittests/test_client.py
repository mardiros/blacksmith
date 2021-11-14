import pytest

from aioli import PathInfoField, Request, Response
from aioli.domain.exceptions import (
    NoContractException,
    TimeoutError,
    UnregisteredResourceException,
    UnregisteredRouteException,
    WrongRequestTypeException,
)
from aioli.domain.model import (
    CollectionParser,
    HTTPAuthorization,
    HTTPRequest,
    HTTPResponse,
    HTTPTimeout,
    HTTPUnauthenticated,
    PostBodyField,
)
from aioli.domain.registry import ApiRoutes, Registry
from aioli.service.base import AbstractTransport
from aioli.service.client import (
    Client,
    ClientFactory,
    CollectionIterator,
    RouteProxy,
    build_timeout,
)
from aioli.typing import HttpMethod


class FakeTransport(AbstractTransport):
    def __init__(self, resp: HTTPResponse) -> None:
        super().__init__()
        self.resp = resp

    async def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
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


def test_build_timeout():
    timeout = build_timeout(HTTPTimeout())
    assert timeout == HTTPTimeout(30.0, 15.0)
    timeout = build_timeout(5.0)
    assert timeout == HTTPTimeout(5.0, 15.0)
    timeout = build_timeout((5.0, 2.0))
    assert timeout == HTTPTimeout(5.0, 2.0)


def test_collection_iterator():
    collec = CollectionIterator(
        HTTPResponse(
            200,
            {"Total-Count": "5"},
            [
                {
                    "name": "Alice",
                    "age": 24,
                    "useless": True,
                },
                {
                    "name": "Bob",
                    "age": 42,
                },
            ],
        ),
        GetResponse,
        CollectionParser,
    )
    assert collec.meta.count == 2
    assert collec.meta.total_count == 5
    list_collec = list(collec)
    assert list_collec == [
        {
            "name": "Alice",
            "age": 24,
        },
        {
            "name": "Bob",
            "age": 42,
        },
    ]


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

    routes = ApiRoutes("/dummies/{name}", {"GET": (GetParam, GetResponse)}, None, None)

    client = Client(
        "api",
        "https://dummies.v1",
        {"dummies": routes},
        transport=FakeTransport(resp),
        auth=HTTPUnauthenticated(),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
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
async def test_client_timeout(static_sd):

    resp = HTTPResponse(
        200,
        {},
        {
            "name": "timeout",
            "age": 42,
        },
    )

    routes = ApiRoutes("/dummies/{name}", {"GET": (GetParam, GetResponse)}, None, None)

    client = Client(
        "api",
        "http://dummies.v1",
        {"dummies": routes},
        transport=FakeTimeoutTransport(),
        auth=HTTPUnauthenticated(),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    with pytest.raises(TimeoutError) as exc:
        await client.dummies.get({"name": "barbie"})
    assert (
        str(exc.value)
        == "ReadTimeout while calling GET http://dummies.v1/dummies/barbie"
    )


@pytest.mark.asyncio
async def test_client_factory(static_sd):
    tp = FakeTimeoutTransport()
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
    resp = HTTPResponse(200, {}, "")
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
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
    resp = HTTPResponse(200, {}, "")
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
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
    resp = HTTPResponse(200, {}, "")
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
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
    resp = HTTPResponse(200, {}, "")
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
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
    resp = HTTPResponse(200, {}, "")
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    resp = await proxy.collection_head({"name": "baby"})
    assert resp == ""


@pytest.mark.asyncio
async def test_route_proxy_collection_get():
    resp = HTTPResponse(
        200, {"Total-Count": "10"}, [{"name": "alice"}, {"name": "bob"}]
    )
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    resp = await proxy.collection_get()
    assert resp.meta.total_count == 10
    assert resp.meta.count == 2
    resp = list(resp)
    assert resp == [{"name": "alice"}, {"name": "bob"}]


@pytest.mark.asyncio
async def test_route_proxy_collection_post():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    resp = await proxy.collection_post({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_collection_put():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    resp = await proxy.collection_put({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_collection_patch():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    resp = await proxy.collection_patch({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_collection_delete():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    resp = await proxy.collection_delete({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_collection_options():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    resp = await proxy.collection_options({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_head():
    resp = HTTPResponse(200, {}, "")
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    resp = await proxy.head({"name": "baby"})
    assert resp == ""


@pytest.mark.asyncio
async def test_route_proxy_get():
    resp = HTTPResponse(200, {}, [{"name": "alice"}, {"name": "bob"}])
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    resp = await proxy.get({})
    assert resp == [{"name": "alice"}, {"name": "bob"}]


@pytest.mark.asyncio
async def test_route_proxy_post():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    resp = await proxy.post({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_put():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    resp = await proxy.put({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_patch():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    resp = await proxy.patch({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_delete():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    resp = await proxy.delete({})
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_options():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
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
        transport=tp,
        auth=HTTPAuthorization("Bearer", "abc"),
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
    )
    resp = await proxy.options({})
    assert resp == {"detail": "accepted"}
