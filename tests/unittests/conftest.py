import pytest
from aioli.domain.model import (
    HTTPAuthorization,
    HTTPRequest,
    HTTPResponse,
)

from aioli.sd.adapters.static import StaticDiscovery, Endpoints
from aioli.sd.adapters.consul import ConsulDiscovery, _registry
from aioli.sd.adapters.router import RouterDiscovery
from aioli.service.base import AbstractTransport
from aioli.service.client import ClientFactory
from aioli.typing import HttpMethod


@pytest.fixture
def static_sd():
    dummy_endpoints: Endpoints = {("dummy", "v1"): "https://dummy.v1/"}
    return StaticDiscovery(dummy_endpoints)


class FakeConsulTransport(AbstractTransport):
    async def request(self, method: HttpMethod, request: HTTPRequest) -> HTTPResponse:
        if request.path["name"] == "dummy-v2":
            return HTTPResponse(200, [])

        return HTTPResponse(
            200,
            [
                {
                    "ServiceAddress": "8.8.8.8",
                    "ServicePort": 1234,
                }
            ],
        )


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
