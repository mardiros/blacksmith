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
from blacksmith.middleware._sync import SyncMiddleware
from blacksmith.middleware._sync.auth import SyncHTTPAuthorizationMiddleware
from blacksmith.middleware._sync.base import SyncHTTPAddHeadersMiddleware
from blacksmith.middleware._sync.http_cache import SyncAbstractCache
from blacksmith.sd._sync.adapters.consul import SyncConsulDiscovery, _registry
from blacksmith.sd._sync.adapters.nomad import SyncNomadDiscovery
from blacksmith.sd._sync.adapters.router import SyncRouterDiscovery
from blacksmith.sd._sync.adapters.static import Endpoints, SyncStaticDiscovery
from blacksmith.service._sync.base import SyncAbstractTransport
from blacksmith.service._sync.client import SyncClientFactory
from blacksmith.typing import ClientName, Path
from tests.unittests.time import SyncSleep


@pytest.fixture
def static_sd() -> SyncStaticDiscovery:
    dummy_endpoints: Endpoints = {("dummy", "v1"): "https://dummy.v1/"}
    return SyncStaticDiscovery(dummy_endpoints)


class FakeConsulTransport(SyncAbstractTransport):
    _body: ClassVar[Sequence[Mapping[str, str | int]]] = [
        {
            "Address": "1.1.1.1",
            "ServiceAddress": "8.8.8.8",
            "ServicePort": 1234,
        }
    ]

    def __call__(
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
def echo_middleware() -> SyncMiddleware:
    def next(
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        return HTTPResponse(200, req.headers, json=json.loads(str(req.body)))

    return next


uncachable_response = echo_middleware


@pytest.fixture
def cachable_response() -> SyncMiddleware:
    def next(
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
def slow_middleware() -> SyncMiddleware:
    def next(
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        SyncSleep(0.06)
        return HTTPResponse(200, req.headers, json=req)

    return next


@pytest.fixture
def boom_middleware() -> SyncMiddleware:
    def next(
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
def invalid_middleware() -> SyncMiddleware:
    def next(
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
def broken_middleware() -> SyncMiddleware:
    def next(
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        raise TypeError("Foo instance has no attibutes bar")

    return next


@pytest.fixture
def authenticated_bearer_middleware() -> SyncMiddleware:
    def next(
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        if req.headers.get("Authorization") != "Bearer abc":
            return HTTPResponse(403, req.headers, json={"detail": "forbidden"})
        return HTTPResponse(200, req.headers, json=json.loads(str(req.body)))

    return next


class SyncDummyMiddleware(SyncHTTPAddHeadersMiddleware):
    def __init__(self) -> None:
        super().__init__(headers={"x-dummy": "test"})
        self.initialized = 0

    def initialize(self) -> None:
        self.initialized += 1


@pytest.fixture
def dummy_middleware() -> SyncHTTPAddHeadersMiddleware:
    return SyncDummyMiddleware()


@pytest.fixture
def consul_sd_with_body(body: dict[str, Any]) -> SyncConsulDiscovery:
    class FakeConsulTransportNoServiceAddr(FakeConsulTransport):
        _body: ClassVar[Sequence[Mapping[str, str | int]]] = [body]

    def cli(url: str, tok: str) -> SyncClientFactory[HTTPError]:
        return SyncClientFactory(
            sd=SyncStaticDiscovery({("consul", "v1"): url}),
            registry=_registry,
            transport=FakeConsulTransportNoServiceAddr(),
        ).add_middleware(SyncHTTPAuthorizationMiddleware("Bearer", tok))

    return SyncConsulDiscovery(_client_factory=cli)


@pytest.fixture
def consul_sd() -> SyncConsulDiscovery:
    def cli(url: str, tok: str) -> SyncClientFactory[HTTPError]:
        return SyncClientFactory(
            sd=SyncStaticDiscovery({("consul", "v1"): url}),
            registry=_registry,
            transport=FakeConsulTransport(),
        ).add_middleware(SyncHTTPAuthorizationMiddleware("Bearer", tok))

    return SyncConsulDiscovery(_client_factory=cli)


@pytest.fixture
def nomad_sd() -> SyncNomadDiscovery:
    return SyncNomadDiscovery()


@pytest.fixture
def router_sd() -> SyncRouterDiscovery:
    return SyncRouterDiscovery()


class SyncFakeHttpMiddlewareCache(SyncAbstractCache):
    """Abstract Redis Client."""

    def __init__(self, data: dict[str, tuple[int, str]] | None = None) -> None:
        super().__init__()
        self.val: dict[str, tuple[int, str]] = data or {}
        self.initialize_called = False

    def initialize(self) -> None:
        self.initialize_called = True

    def get(self, key: str) -> str | None:
        """Get a value from redis"""
        try:
            return self.val[key][1]
        except KeyError:
            return None

    def set(self, key: str, val: str, ex: timedelta) -> None:
        """Get a value from redis"""
        self.val[key] = (ex.seconds, val)


@pytest.fixture
def fake_http_middleware_cache() -> SyncFakeHttpMiddlewareCache:
    return SyncFakeHttpMiddlewareCache()


@pytest.fixture
def fake_http_middleware_cache_with_data(
    params: Mapping[str, Any],
) -> SyncFakeHttpMiddlewareCache:
    return SyncFakeHttpMiddlewareCache(params["initial_cache"])


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
