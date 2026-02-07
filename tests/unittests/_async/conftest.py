import json
import logging
from collections.abc import Mapping, Sequence
from datetime import timedelta
from typing import (
    Any,
    ClassVar,
    Literal,
)

import pytest

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.model.middleware.zipkin import AbstractTraceContext
from blacksmith.middleware._async import AsyncMiddleware
from blacksmith.middleware._async.auth import AsyncHTTPAuthorizationMiddleware
from blacksmith.middleware._async.base import AsyncHTTPAddHeadersMiddleware
from blacksmith.middleware._async.http_cache import AsyncAbstractCache
from blacksmith.sd._async.adapters.consul import AsyncConsulDiscovery, _registry
from blacksmith.sd._async.adapters.nomad import AsyncNomadDiscovery
from blacksmith.sd._async.adapters.router import AsyncRouterDiscovery
from blacksmith.sd._async.adapters.static import AsyncStaticDiscovery, Endpoints
from blacksmith.service._async.base import AsyncAbstractTransport
from blacksmith.service._async.client import AsyncClientFactory
from blacksmith.typing import ClientName, Path
from tests.unittests.time import AsyncSleep


@pytest.fixture
def static_sd() -> AsyncStaticDiscovery:
    dummy_endpoints: Endpoints = {("dummy", "v1"): "https://dummy.v1/"}
    return AsyncStaticDiscovery(dummy_endpoints)


class FakeConsulTransport(AsyncAbstractTransport):
    _body: ClassVar[Sequence[Mapping[str, str | int]]] = [
        {
            "Address": "1.1.1.1",
            "ServiceAddress": "8.8.8.8",
            "ServicePort": 1234,
        }
    ]

    async def __call__(
        self,
        request: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        if request.path["name"] == "dummy-v2":
            return HTTPResponse(200, {}, [])

        if request.path["name"] == "dummy-v3":
            raise HTTPError(
                "422 Unprocessable entity",
                request,
                HTTPResponse(422, {}, {"detail": "error"}),
            )

        return HTTPResponse(
            200,
            {},
            self._body,
        )


@pytest.fixture
def echo_middleware() -> AsyncMiddleware:
    async def next(
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        return HTTPResponse(200, req.headers, json=json.loads(str(req.body)))

    return next


uncachable_response = echo_middleware


@pytest.fixture
def cachable_response() -> AsyncMiddleware:
    async def next(
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        return HTTPResponse(
            200, {"cache-control": "max-age=42, public"}, json="Cache Me"
        )

    return next


@pytest.fixture
def slow_middleware() -> AsyncMiddleware:
    async def next(
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        await AsyncSleep(0.06)
        return HTTPResponse(200, req.headers, json=req)

    return next


@pytest.fixture
def boom_middleware() -> AsyncMiddleware:
    async def next(
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        raise HTTPError(
            "Boom", req, HTTPResponse(500, {}, json={"detail": "I am bored"})
        )

    return next


@pytest.fixture
def invalid_middleware() -> AsyncMiddleware:
    async def next(
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        raise HTTPError(
            "Boom",
            req,
            HTTPResponse(422, {}, json={"detail": "What are you talking about?"}),
        )

    return next


@pytest.fixture
def broken_middleware() -> AsyncMiddleware:
    async def next(
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        raise TypeError("Foo instance has no attibutes bar")

    return next


@pytest.fixture
def authenticated_bearer_middleware() -> AsyncMiddleware:
    async def next(
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        if req.headers.get("Authorization") != "Bearer abc":
            return HTTPResponse(403, req.headers, json={"detail": "forbidden"})
        return HTTPResponse(200, req.headers, json=json.loads(str(req.body)))

    return next


class AsyncDummyMiddleware(AsyncHTTPAddHeadersMiddleware):
    def __init__(self) -> None:
        super().__init__(headers={"x-dummy": "test"})
        self.initialized = 0

    async def initialize(self) -> None:
        self.initialized += 1


@pytest.fixture
def dummy_middleware() -> AsyncHTTPAddHeadersMiddleware:
    return AsyncDummyMiddleware()


@pytest.fixture
def consul_sd_with_body(body: dict[str, Any]) -> AsyncConsulDiscovery:
    class FakeConsulTransportNoServiceAddr(FakeConsulTransport):
        _body: ClassVar[Sequence[Mapping[str, str | int]]] = [body]

    def cli(url: str, tok: str) -> AsyncClientFactory[HTTPError]:
        return AsyncClientFactory(
            sd=AsyncStaticDiscovery({("consul", "v1"): url}),
            registry=_registry,
            transport=FakeConsulTransportNoServiceAddr(),
        ).add_middleware(AsyncHTTPAuthorizationMiddleware("Bearer", tok))

    return AsyncConsulDiscovery(_client_factory=cli)


@pytest.fixture
def consul_sd() -> AsyncConsulDiscovery:
    def cli(url: str, tok: str) -> AsyncClientFactory[HTTPError]:
        return AsyncClientFactory(
            sd=AsyncStaticDiscovery({("consul", "v1"): url}),
            registry=_registry,
            transport=FakeConsulTransport(),
        ).add_middleware(AsyncHTTPAuthorizationMiddleware("Bearer", tok))

    return AsyncConsulDiscovery(_client_factory=cli)


@pytest.fixture
def nomad_sd() -> AsyncNomadDiscovery:
    return AsyncNomadDiscovery()


@pytest.fixture
def router_sd() -> AsyncRouterDiscovery:
    return AsyncRouterDiscovery()


class AsyncFakeHttpMiddlewareCache(AsyncAbstractCache):
    """Abstract Redis Client."""

    def __init__(self, data: dict[str, tuple[int, str]] | None = None) -> None:
        super().__init__()
        self.val: dict[str, tuple[int, str]] = data or {}
        self.initialize_called = False

    async def initialize(self) -> None:
        self.initialize_called = True

    async def get(self, key: str) -> str | None:
        """Get a value from redis"""
        try:
            return self.val[key][1]
        except KeyError:
            return None

    async def set(self, key: str, val: str, ex: timedelta) -> None:
        """Get a value from redis"""
        self.val[key] = (ex.seconds, val)


@pytest.fixture
def fake_http_middleware_cache() -> AsyncFakeHttpMiddlewareCache:
    return AsyncFakeHttpMiddlewareCache()


@pytest.fixture
def fake_http_middleware_cache_with_data(
    params: Mapping[str, Any],
) -> AsyncFakeHttpMiddlewareCache:
    return AsyncFakeHttpMiddlewareCache(params["initial_cache"])


class Trace(AbstractTraceContext):
    name: str
    kind: str
    tags: dict[str, str]
    annotations: list[tuple[str | None, float | None]]

    def __init__(self, name: str, kind: str) -> None:
        Trace.name = name
        Trace.kind = kind
        Trace.tags = {}
        Trace.annotations = []

    @classmethod
    def make_headers(cls) -> dict[str, str]:
        return {}

    def __enter__(self) -> "Trace":
        return self

    def __exit__(self, *exc: Any) -> None:
        pass

    def tag(self, key: str, value: str) -> "Trace":
        Trace.tags[key] = value
        return self

    def annotate(self, value: str | None, ts: float | None = None) -> "Trace":
        Trace.annotations.append((value, ts))
        return self


@pytest.fixture
def trace() -> type[AbstractTraceContext]:
    return Trace


class FakeLogger:
    logs: list[tuple[Literal["debug", "info", "error"], str, Any]]

    def __init__(self, name: str, *, level: int = logging.INFO) -> None:
        self.level = level
        self.logs = []

    def isEnabledFor(self, level: int) -> bool:
        return level >= self.level

    def debug(self, logline: Any, *args: Any) -> None:
        if self.isEnabledFor(logging.DEBUG):
            self.logs.append(("debug", logline, args[:-1]))  # drop the time

    def info(self, logline: Any, *args: Any) -> None:
        if self.isEnabledFor(logging.INFO):
            self.logs.append(("info", logline, args[:-1]))  # drop the time

    def error(self, logline: Any, *args: Any) -> None:
        if self.isEnabledFor(logging.ERROR):
            self.logs.append(("error", logline, args[:-1]))  # drop the time


@pytest.fixture
def logger() -> type[FakeLogger]:
    return FakeLogger
