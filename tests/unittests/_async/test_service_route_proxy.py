from typing import Any

import pytest

from blacksmith import Request
from blacksmith.domain.exceptions import (
    HTTPError,
    NoContractException,
    UnregisteredRouteException,
    WrongRequestTypeException,
)
from blacksmith.domain.model import (
    CollectionParser,
    HTTPRequest,
    HTTPResponse,
    HTTPTimeout,
)
from blacksmith.domain.model.params import CollectionIterator
from blacksmith.domain.registry import ApiRoutes
from blacksmith.middleware._async.auth import AsyncHTTPAuthorization
from blacksmith.middleware._async.base import AsyncHTTPAddHeadersMiddleware
from blacksmith.service._async.base import AsyncAbstractTransport
from blacksmith.service._async.route_proxy import AsyncRouteProxy, build_timeout
from blacksmith.typing import ClientName, Path
from tests.unittests.dummy_registry import GetParam, GetResponse, PostParam


class FakeTransport(AsyncAbstractTransport):
    def __init__(self, resp: HTTPResponse) -> None:
        super().__init__()
        self.resp = resp

    async def __call__(
        self,
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:

        if self.resp.status_code >= 400:
            raise HTTPError(f"{self.resp.status_code} blah", req, self.resp)
        return self.resp


def test_build_timeout():
    timeout = build_timeout(HTTPTimeout())
    assert timeout == HTTPTimeout(30.0, 15.0)
    timeout = build_timeout(5.0)
    assert timeout == HTTPTimeout(5.0, 15.0)
    timeout = build_timeout((5.0, 2.0))
    assert timeout == HTTPTimeout(5.0, 2.0)


@pytest.mark.asyncio
async def test_route_proxy_prepare_middleware(
    dummy_http_request: HTTPRequest, echo_middleware: AsyncAbstractTransport
):
    resp = HTTPResponse(200, {}, "")

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"GET": (Request, None)},
            collection_path=None,
            collection_contract=None,
            collection_parser=None,
        ),
        transport=echo_middleware,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[
            AsyncHTTPAuthorization("Bearer", "abc"),
            AsyncHTTPAddHeadersMiddleware({"foo": "bar"}),
            AsyncHTTPAddHeadersMiddleware({"Eggs": "egg"}),
        ],
    )
    resp = await proxy._handle_req_with_middlewares(
        dummy_http_request,
        HTTPTimeout(4.2),
        "/",
    )
    assert resp.headers == {
        "Authorization": "Bearer abc",
        "X-Req-Id": "42",
        "Eggs": "egg",
        "foo": "bar",
    }


@pytest.mark.asyncio
async def test_route_proxy_prepare_unregistered_method_resource():
    resp = HTTPResponse(200, {}, "")
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={},
            collection_path=None,
            collection_contract=None,
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    with pytest.raises(NoContractException) as exc:
        resp = proxy._prepare_request("GET", {}, proxy.routes.resource)
    assert (
        str(exc.value)
        == "Unregistered route 'GET' in resource 'dummies' in client 'dummy'"
    )


@pytest.mark.asyncio
async def test_route_proxy_prepare_unregistered_method_collection():
    resp = HTTPResponse(200, {}, "")
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            "/",
            {},
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    with pytest.raises(NoContractException) as exc:
        resp = proxy._prepare_request("GET", {}, proxy.routes.collection)
    assert (
        str(exc.value)
        == "Unregistered route 'GET' in resource 'dummies' in client 'dummy'"
    )


@pytest.mark.asyncio
async def test_route_proxy_prepare_unregistered_resource():
    resp = HTTPResponse(200, {}, "")
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            "/",
            {},
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    with pytest.raises(UnregisteredRouteException) as exc:
        resp = proxy._prepare_request("GET", {}, proxy.routes.resource)
    assert (
        str(exc.value)
        == "Unregistered route 'GET' in resource 'dummies' in client 'dummy'"
    )


@pytest.mark.asyncio
async def test_route_proxy_prepare_unregistered_collection():
    resp = HTTPResponse(200, {}, "")
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            "/",
            {},
            None,
            None,
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    with pytest.raises(UnregisteredRouteException) as exc:
        resp = proxy._prepare_request("GET", {}, proxy.routes.collection)
    assert (
        str(exc.value)
        == "Unregistered route 'GET' in resource 'dummies' in client 'dummy'"
    )


@pytest.mark.asyncio
async def test_route_proxy_prepare_wrong_type():
    resp = HTTPResponse(200, {}, "")
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            "/",
            {"GET": (GetParam, GetResponse)},
            None,
            None,
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    with pytest.raises(WrongRequestTypeException) as exc:
        resp = proxy._prepare_request(
            "GET", PostParam(name="barbie", age=42), proxy.routes.resource
        )

    assert (
        str(exc.value) == "Invalid type 'tests.unittests.dummy_registry.PostParam' "
        "for route 'GET' in resource 'dummies' in client 'dummy'"
    )


@pytest.mark.asyncio
async def test_route_proxy_collection_head():
    resp = HTTPResponse(200, {}, "")
    tp = FakeTransport(resp)
    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"HEAD": (Request, None)},
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp = (await proxy.collection_head({"name": "baby"})).json
    assert resp == ""


@pytest.mark.asyncio
async def test_route_proxy_collection_get():
    httpresp = HTTPResponse(
        200, {"Total-Count": "10"}, [{"name": "alice"}, {"name": "bob"}]
    )
    tp = FakeTransport(httpresp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"GET": (Request, None)},
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp: CollectionIterator[Any] = await proxy.collection_get()
    assert resp.meta.total_count == 10
    assert resp.meta.count == 2
    lresp = list(resp)
    assert lresp == [{"name": "alice"}, {"name": "bob"}]


@pytest.mark.asyncio
async def test_route_proxy_collection_get_with_parser():
    class MyCollectionParser(CollectionParser):
        total_count_header: str = "X-Total-Count"

    httpresp = HTTPResponse(
        200, {"X-Total-Count": "10"}, [{"name": "alice"}, {"name": "bob"}]
    )
    tp = FakeTransport(httpresp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"GET": (Request, None)},
            collection_parser=MyCollectionParser,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp: CollectionIterator[Any] = await proxy.collection_get()
    assert resp.meta.total_count == 10
    assert resp.meta.count == 2
    lresp = list(resp)
    assert lresp == [{"name": "alice"}, {"name": "bob"}]


@pytest.mark.asyncio
async def test_route_proxy_collection_post():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"POST": (Request, None)},
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp = (await proxy.collection_post({})).json
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_collection_put():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"PUT": (Request, None)},
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp = (await proxy.collection_put({})).json
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_collection_patch():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"PATCH": (Request, None)},
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp = (await proxy.collection_patch({})).json
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_collection_delete():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"DELETE": (Request, None)},
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp = (await proxy.collection_delete({})).json
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_collection_options():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            None,
            None,
            collection_path="/",
            collection_contract={"OPTIONS": (Request, None)},
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp = (await proxy.collection_options({})).json
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_head():
    resp = HTTPResponse(200, {}, "")
    tp = FakeTransport(resp)
    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"HEAD": (Request, None)},
            collection_contract=None,
            collection_path=None,
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp = (await proxy.head({"name": "baby"})).json
    assert resp == ""


@pytest.mark.asyncio
async def test_route_proxy_get():
    resp = HTTPResponse(200, {}, [{"name": "alice"}, {"name": "bob"}])
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"GET": (Request, None)},
            collection_contract=None,
            collection_path=None,
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp = (await proxy.get({})).json
    assert resp == [{"name": "alice"}, {"name": "bob"}]


@pytest.mark.asyncio
async def test_route_proxy_post():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"POST": (Request, None)},
            collection_contract=None,
            collection_path=None,
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp = (await proxy.post({})).json
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_put():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"PUT": (Request, None)},
            collection_contract=None,
            collection_path=None,
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp = (await proxy.put({})).json
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_patch():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"PATCH": (Request, None)},
            collection_contract=None,
            collection_path=None,
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp = (await proxy.patch({})).json
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_delete():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"DELETE": (Request, None)},
            collection_contract=None,
            collection_path=None,
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp = (await proxy.delete({})).json
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_route_proxy_options():
    resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(resp)

    proxy = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"OPTIONS": (Request, None)},
            collection_contract=None,
            collection_path=None,
            collection_parser=None,
        ),
        transport=tp,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[],
    )
    resp = (await proxy.options({})).json
    assert resp == {"detail": "accepted"}


@pytest.mark.asyncio
async def test_unregistered_collection(echo_middleware: AsyncAbstractTransport):
    proxy: AsyncRouteProxy[Any, Any] = AsyncRouteProxy(
        "dummy",
        "dummies",
        "http://dummy/",
        ApiRoutes(
            path="/",
            contract={"GET": (Request, None)},
            collection_path=None,
            collection_contract=None,
            collection_parser=None,
        ),
        transport=echo_middleware,
        timeout=HTTPTimeout(),
        collection_parser=CollectionParser,
        middlewares=[
            AsyncHTTPAuthorization("Bearer", "abc"),
            AsyncHTTPAddHeadersMiddleware({"foo": "bar"}),
            AsyncHTTPAddHeadersMiddleware({"Eggs": "egg"}),
        ],
    )
    for verb in ("get", "post", "put", "patch", "delete", "options", "head"):
        with pytest.raises(UnregisteredRouteException) as ctx:
            meth = getattr(proxy, f"collection_{verb}")
            await meth({})
        assert (
            str(ctx.value) == f"Unregistered route '{verb.upper()}' "
            f"in resource 'dummies' in client 'dummy'"
        )
