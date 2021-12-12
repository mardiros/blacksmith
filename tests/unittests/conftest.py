import time
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

import pytest

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.middleware.auth import HTTPAuthorization
from blacksmith.middleware.base import HTTPAddHeadersMiddleware
from blacksmith.sd.adapters.consul import ConsulDiscovery, _registry
from blacksmith.sd.adapters.router import RouterDiscovery
from blacksmith.sd.adapters.static import Endpoints, StaticDiscovery
from blacksmith.service.base import AbstractTransport
from blacksmith.service.client import ClientFactory
from blacksmith.typing import ClientName, HttpMethod, Path


@pytest.fixture
def static_sd():
    dummy_endpoints: Endpoints = {("dummy", "v1"): "https://dummy.v1/"}
    return StaticDiscovery(dummy_endpoints)


class FakeConsulTransport(AbstractTransport):
    async def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
        if request.path["name"] == "dummy-v2":
            return HTTPResponse(200, {}, [])

        if request.path["name"] == "dummy-v3":
            raise HTTPError(
                f"422 Unprocessable entity",
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


class EchoTransport(AbstractTransport):
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
def slow_middleware():
    async def next(
        req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
    ) -> HTTPResponse:
        time.sleep(0.06)
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


@pytest.fixture
def dummy_http_request():
    return HTTPRequest(
        "/dummy/{name}",
        {"name": 42},
        {"foo": "bar"},
        {"X-Req-Id": "42"},
        '{"bandi_manchot": "777"}',
    )


class DummyMiddleware(HTTPAddHeadersMiddleware):
    def __init__(self):
        super().__init__(headers={"x-dummy": "test"})


@pytest.fixture
def dummy_middleware():
    return DummyMiddleware()


@pytest.fixture
def consul_sd():
    def cli(url: str, tok: str) -> ClientFactory:
        return ClientFactory(
            sd=StaticDiscovery({("consul", "v1"): url}),
            registry=_registry,
            transport=FakeConsulTransport(),
        ).add_middleware(HTTPAuthorization("Bearer", tok))

    return ConsulDiscovery(_client_factory=cli)


@pytest.fixture
def router_sd():
    return RouterDiscovery()
