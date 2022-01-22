from datetime import timedelta
from typing import Any, Dict, Mapping, Optional, Tuple

import pytest

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.middleware._sync.auth import SyncHTTPAuthorization
from blacksmith.middleware._sync.base import SyncHTTPAddHeadersMiddleware
from blacksmith.middleware._sync.http_cache import SyncAbstractCache
from blacksmith.sd._sync.adapters.consul import SyncConsulDiscovery, _registry
from blacksmith.sd._sync.adapters.router import SyncRouterDiscovery
from blacksmith.sd._sync.adapters.static import Endpoints, SyncStaticDiscovery
from blacksmith.service._sync.base import SyncAbstractTransport
from blacksmith.service._sync.client import SyncClientFactory
from blacksmith.typing import ClientName, Path
from tests.unittests.time import SyncSleep


@pytest.fixture
def static_sd():
    dummy_endpoints: Endpoints = {("dummy", "v1"): "https://dummy.v1/"}
    return SyncStaticDiscovery(dummy_endpoints)


class FakeConsulTransport(SyncAbstractTransport):
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
            [
                {
                    "ServiceAddress": "8.8.8.8",
                    "ServicePort": 1234,
                }
            ],
        )


@pytest.fixture
def echo_middleware():
    def next(
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        return HTTPResponse(200, req.headers, json=req)

    return next


uncachable_response = echo_middleware


@pytest.fixture
def cachable_response():
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
def slow_middleware():
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
def boom_middleware():
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
def invalid_middleware():
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


class SyncDummyMiddleware(SyncHTTPAddHeadersMiddleware):
    def __init__(self):
        super().__init__(headers={"x-dummy": "test"})
        self.initialized = 0

    def initialize(self):
        self.initialized += 1


@pytest.fixture
def dummy_middleware():
    return SyncDummyMiddleware()


@pytest.fixture
def consul_sd():
    def cli(url: str, tok: str) -> SyncClientFactory[Any, Any]:
        return SyncClientFactory(
            sd=SyncStaticDiscovery({("consul", "v1"): url}),
            registry=_registry,
            transport=FakeConsulTransport(),
        ).add_middleware(SyncHTTPAuthorization("Bearer", tok))

    return SyncConsulDiscovery(_client_factory=cli)


@pytest.fixture
def router_sd():
    return SyncRouterDiscovery()


class SyncFakeHttpMiddlewareCache(SyncAbstractCache):
    """Abstract Redis Client."""

    def __init__(self, data: Optional[Dict[str, Tuple[int, str]]] = None) -> None:
        super().__init__()
        self.val: Dict[str, Tuple[int, str]] = data or {}
        self.initialize_called = False

    def initialize(self):
        self.initialize_called = True

    def get(self, key: str) -> Optional[str]:
        """Get a value from redis"""
        try:
            return self.val[key][1]
        except KeyError:
            return None

    def set(self, key: str, val: str, ex: timedelta):
        """Get a value from redis"""
        self.val[key] = (ex.seconds, val)


@pytest.fixture
def fake_http_middleware_cache():
    return SyncFakeHttpMiddlewareCache()


@pytest.fixture
def fake_http_middleware_cache_with_data(params: Mapping[str, Any]):
    return SyncFakeHttpMiddlewareCache(params["initial_cache"])
