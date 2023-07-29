from typing import Any

import pytest
from pydantic import BaseModel, Field
from result import Result

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
from blacksmith.middleware._async.auth import AsyncHTTPAuthorizationMiddleware
from blacksmith.middleware._async.base import AsyncHTTPAddHeadersMiddleware
from blacksmith.service._async.base import AsyncAbstractTransport
from blacksmith.service._async.route_proxy import AsyncRouteProxy, build_timeout
from blacksmith.typing import ClientName, Path
from tests.unittests.dummy_registry import GetParam, GetResponse, PostParam


class MyErrorFormat(BaseModel):
    message: str = Field(...)
    detail: str = Field(...)


def error_parser(error: HTTPError) -> MyErrorFormat:
    return MyErrorFormat(**error.json)  # type: ignore


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


def test_build_timeout() -> None:
    timeout = build_timeout(HTTPTimeout())
    assert timeout == HTTPTimeout(30.0, 15.0)
    timeout = build_timeout(5.0)
    assert timeout == HTTPTimeout(5.0, 15.0)
    timeout = build_timeout((5.0, 2.0))
    assert timeout == HTTPTimeout(5.0, 2.0)


async def test_route_proxy_prepare_middleware(
    dummy_http_request: HTTPRequest, echo_middleware: AsyncAbstractTransport
):
    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
            AsyncHTTPAuthorizationMiddleware("Bearer", "abc"),
            AsyncHTTPAddHeadersMiddleware({"foo": "bar"}),
            AsyncHTTPAddHeadersMiddleware({"Eggs": "egg"}),
        ],
        error_parser=error_parser,
    )
    result = await proxy._handle_req_with_middlewares(
        dummy_http_request,
        HTTPTimeout(4.2),
        "/",
    )
    assert result.is_ok()
    resp = result.unwrap()
    assert resp.headers == {
        "Authorization": "Bearer abc",
        "X-Req-Id": "42",
        "Eggs": "egg",
        "foo": "bar",
    }


async def test_route_proxy_prepare_unregistered_method_resource() -> None:
    http_resp = HTTPResponse(200, {}, "")
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    with pytest.raises(NoContractException) as exc:
        proxy._prepare_request("GET", {}, proxy.routes.resource)
    assert (
        str(exc.value)
        == "Unregistered route 'GET' in resource 'dummies' in client 'dummy'"
    )


async def test_route_proxy_prepare_unregistered_method_collection() -> None:
    http_resp = HTTPResponse(200, {}, "")
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    with pytest.raises(NoContractException) as exc:
        proxy._prepare_request("GET", {}, proxy.routes.collection)
    assert (
        str(exc.value)
        == "Unregistered route 'GET' in resource 'dummies' in client 'dummy'"
    )


async def test_route_proxy_prepare_unregistered_resource() -> None:
    http_resp = HTTPResponse(200, {}, "")
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    with pytest.raises(UnregisteredRouteException) as exc:
        proxy._prepare_request("GET", {}, proxy.routes.resource)
    assert (
        str(exc.value)
        == "Unregistered route 'GET' in resource 'dummies' in client 'dummy'"
    )


async def test_route_proxy_prepare_unregistered_collection() -> None:
    http_resp = HTTPResponse(200, {}, "")
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    with pytest.raises(UnregisteredRouteException) as exc:
        proxy._prepare_request("GET", {}, proxy.routes.collection)
    assert (
        str(exc.value)
        == "Unregistered route 'GET' in resource 'dummies' in client 'dummy'"
    )


async def test_route_proxy_prepare_wrong_type() -> None:
    http_resp = HTTPResponse(200, {}, "")
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    with pytest.raises(WrongRequestTypeException) as exc:
        proxy._prepare_request(
            "GET", PostParam(name="barbie", age=42), proxy.routes.resource
        )

    assert (
        str(exc.value) == "Invalid type 'tests.unittests.dummy_registry.PostParam' "
        "for route 'GET' in resource 'dummies' in client 'dummy'"
    )


async def test_route_proxy_collection_head() -> None:
    http_resp = HTTPResponse(200, {}, "")
    tp = FakeTransport(http_resp)
    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    resp = (await proxy.collection_head({"name": "baby"})).json
    assert resp == ""


async def test_route_proxy_collection_get() -> None:
    httpresp = HTTPResponse(
        200, {"Total-Count": "10"}, [{"name": "alice"}, {"name": "bob"}]
    )
    tp = FakeTransport(httpresp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    result: Result[
        CollectionIterator[Any], MyErrorFormat
    ] = await proxy.collection_get()
    assert result.is_ok()
    resp = result.unwrap()
    assert resp.meta.total_count == 10
    assert resp.meta.count == 2
    lresp = list(resp)  # type: ignore
    assert lresp == [{"name": "alice"}, {"name": "bob"}]


async def test_route_proxy_collection_get_with_parser() -> None:
    class MyCollectionParser(CollectionParser):
        total_count_header: str = "X-Total-Count"

    httpresp = HTTPResponse(
        200, {"X-Total-Count": "10"}, [{"name": "alice"}, {"name": "bob"}]
    )
    tp = FakeTransport(httpresp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    result: Result[
        CollectionIterator[Any], MyErrorFormat
    ] = await proxy.collection_get()
    assert result.is_ok()
    resp = result.unwrap()
    assert resp.meta.total_count == 10
    assert resp.meta.count == 2
    lresp = list(resp)  # type: ignore
    assert lresp == [{"name": "alice"}, {"name": "bob"}]


async def test_route_proxy_collection_post() -> None:
    http_resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    resp = (await proxy.collection_post({})).json
    assert resp == {"detail": "accepted"}


async def test_route_proxy_collection_put() -> None:
    http_resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    resp = (await proxy.collection_put({})).json
    assert resp == {"detail": "accepted"}


async def test_route_proxy_collection_patch() -> None:
    http_resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    resp = (await proxy.collection_patch({})).json
    assert resp == {"detail": "accepted"}


async def test_route_proxy_collection_delete() -> None:
    http_resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    resp = (await proxy.collection_delete({})).json
    assert resp == {"detail": "accepted"}


async def test_route_proxy_collection_options() -> None:
    http_resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    resp = (await proxy.collection_options({})).json
    assert resp == {"detail": "accepted"}


async def test_route_proxy_head() -> None:
    http_resp = HTTPResponse(200, {}, "")
    tp = FakeTransport(http_resp)
    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    resp = (await proxy.head({"name": "baby"})).json
    assert resp == ""


async def test_route_proxy_get() -> None:
    http_resp = HTTPResponse(200, {}, [{"name": "alice"}, {"name": "bob"}])
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    resp = (await proxy.get({})).json
    assert resp == [{"name": "alice"}, {"name": "bob"}]


async def test_route_proxy_post() -> None:
    http_resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    resp = (await proxy.post({})).json
    assert resp == {"detail": "accepted"}


async def test_route_proxy_put() -> None:
    http_resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    resp = (await proxy.put({})).json
    assert resp == {"detail": "accepted"}


async def test_route_proxy_patch() -> None:
    http_resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    resp = (await proxy.patch({})).json
    assert resp == {"detail": "accepted"}


async def test_route_proxy_delete() -> None:
    http_resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    resp = (await proxy.delete({})).json
    assert resp == {"detail": "accepted"}


async def test_route_proxy_options() -> None:
    http_resp = HTTPResponse(202, {}, {"detail": "accepted"})
    tp = FakeTransport(http_resp)

    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
        error_parser=error_parser,
    )
    resp = (await proxy.options({})).json
    assert resp == {"detail": "accepted"}


async def test_unregistered_collection(echo_middleware: AsyncAbstractTransport):
    proxy: AsyncRouteProxy[Any, Any, Any] = AsyncRouteProxy(
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
            AsyncHTTPAuthorizationMiddleware("Bearer", "abc"),
            AsyncHTTPAddHeadersMiddleware({"foo": "bar"}),
            AsyncHTTPAddHeadersMiddleware({"Eggs": "egg"}),
        ],
        error_parser=error_parser,
    )
    for verb in ("get", "post", "put", "patch", "delete", "options", "head"):
        with pytest.raises(UnregisteredRouteException) as ctx:
            meth = getattr(proxy, f"collection_{verb}")
            await meth({})
        assert (
            str(ctx.value) == f"Unregistered route '{verb.upper()}' "
            f"in resource 'dummies' in client 'dummy'"
        )
