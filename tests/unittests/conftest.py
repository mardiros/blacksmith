from collections import Counter, defaultdict
from typing import Dict, List, Tuple
import pytest
from aioli.domain.exceptions import HTTPError
from aioli.domain.model import (
    HTTPAuthorization,
    HTTPMiddleware,
    HTTPRequest,
    HTTPResponse,
    HTTPTimeout,
)

from aioli.monitoring.base import AbstractMetricsCollector
from aioli.sd.adapters.static import StaticDiscovery, Endpoints
from aioli.sd.adapters.consul import ConsulDiscovery, _registry
from aioli.sd.adapters.router import RouterDiscovery
from aioli.service.base import AbstractTransport
from aioli.service.client import ClientFactory
from aioli.typing import ClientName, HttpMethod


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


class DummyMetricsCollector(AbstractMetricsCollector):
    def __init__(self) -> None:
        self.counter = Counter()
        self.duration: Dict[Tuple, List[float]] = defaultdict(list)

    def observe_request(
        self,
        client_name: ClientName,
        method: HttpMethod,
        path: str,
        status_code: int,
        duration: float,
    ):
        self.counter[(client_name, method, path, status_code)] += 1
        self.duration[(client_name, method, path, status_code)].append(duration)


@pytest.fixture
def dummy_metrics_collector():
    return DummyMetricsCollector()


class DummyMiddleware(HTTPMiddleware):
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
            auth=HTTPAuthorization("Bearer", tok),
            transport=FakeConsulTransport(),
        )

    return ConsulDiscovery(_client_factory=cli)


@pytest.fixture
def router_sd():
    return RouterDiscovery()
