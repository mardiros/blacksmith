from tests.unittests.time import AsyncSleep
from datetime import timedelta
from typing import Dict, Optional, Tuple

import pytest

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.middleware._async.auth import AsyncHTTPAuthorization
from blacksmith.middleware._async.base import AsyncHTTPAddHeadersMiddleware
from blacksmith.middleware._async.http_caching import AsyncAbstractCache
from blacksmith.sd._async.adapters.consul import AsyncConsulDiscovery, _registry
from blacksmith.sd._async.adapters.router import AsyncRouterDiscovery
from blacksmith.sd._async.adapters.static import AsyncStaticDiscovery, Endpoints
from blacksmith.service._async.base import AsyncAbstractTransport
from blacksmith.service._async.client import AsyncClientFactory
from blacksmith.typing import ClientName, HttpMethod, Path


@pytest.fixture
def static_sd():
    dummy_endpoints: Endpoints = {("dummy", "v1"): "https://dummy.v1/"}
    return AsyncStaticDiscovery(dummy_endpoints)


class FakeConsulTransport(AsyncAbstractTransport):
    async def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
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


class EchoTransport(AsyncAbstractTransport):
    def __init__(self) -> None:
        super().__init__()

    async def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
        return HTTPResponse(200, request.headers, request)


@pytest.fixture
def echo_transport():
    return EchoTransport()


@pytest.fixture
def echo_middleware():
    async def next(
        req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
    ) -> HTTPResponse:
        return HTTPResponse(200, req.headers, json=req)

    return next


@pytest.fixture
def cachable_response():
    async def next(
        req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
    ) -> HTTPResponse:
        return HTTPResponse(
            200, {"cache-control": "max-age=42, public"}, json="Cache Me"
        )

    return next


@pytest.fixture
def slow_middleware():
    async def next(
        req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
    ) -> HTTPResponse:
        await AsyncSleep(0.06)
        return HTTPResponse(200, req.headers, json=req)

    return next


@pytest.fixture
def boom_middleware():
    async def next(
        req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
    ) -> HTTPResponse:
        raise HTTPError(
            "Boom", req, HTTPResponse(500, {}, json={"detail": "I am bored"})
        )

    return next


@pytest.fixture
def invalid_middleware():
    async def next(
        req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
    ) -> HTTPResponse:
        raise HTTPError(
            "Boom",
            req,
            HTTPResponse(422, {}, json={"detail": "What are you talking about?"}),
        )

    return next


class AsyncDummyMiddleware(AsyncHTTPAddHeadersMiddleware):
    def __init__(self):
        super().__init__(headers={"x-dummy": "test"})
        self.initialized = 0

    async def initialize(self):
        self.initialized += 1


@pytest.fixture
def dummy_middleware():
    return AsyncDummyMiddleware()


@pytest.fixture
def consul_sd():
    def cli(url: str, tok: str) -> AsyncClientFactory:
        return AsyncClientFactory(
            sd=AsyncStaticDiscovery({("consul", "v1"): url}),
            registry=_registry,
            transport=FakeConsulTransport(),
        ).add_middleware(AsyncHTTPAuthorization("Bearer", tok))

    return AsyncConsulDiscovery(_client_factory=cli)


@pytest.fixture
def router_sd():
    return AsyncRouterDiscovery()


class AsyncFakeHttpMiddlewareCache(AsyncAbstractCache):
    """Abstract Redis Client."""

    def __init__(self) -> None:
        super().__init__()
        self.val: Dict[str, Tuple[int, str]] = {}

    async def initialize(self):
        pass

    async def get(self, key: str) -> Optional[str]:
        """Get a value from redis"""
        try:
            return self.val[key][1]
        except KeyError:
            return None

    async def set(self, key: str, val: str, ex: timedelta):
        """Get a value from redis"""
        self.val[key] = (ex.seconds, val)


@pytest.fixture
def fake_http_middleware_cache():
    return AsyncFakeHttpMiddlewareCache()
