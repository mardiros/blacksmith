from typing import Any, Coroutine

import pytest
from fastapi.testclient import TestClient

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.service._async.base import AsyncAbstractTransport

from notif.views import fastapi
from notif.config import AppConfig, FastConfig


class FakeTransport(AsyncAbstractTransport):
    def __init__(self, responses):
        super().__init__()
        self.responses = responses

    async def __call__(
        self,
        req: HTTPRequest,
        client_name: str,
        path: str,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        """This is the next function of the middleware."""
        return self.responses[f"{req.method} {req.url}"]


@pytest.fixture
def settings():
    return {
        "service_url_fmt": "http://{service}.{version}",
        "unversioned_service_url_fmt": "http://{service}",
    }


@pytest.fixture
@pytest.mark.asyncio
async def configure_dependency_injection(params, settings):
    settings["transport"] = FakeTransport(params["blacksmith_responses"])
    await FastConfig.configure(settings)
    yield

@pytest.fixture
def client(configure_dependency_injection):
    client = TestClient(fastapi)
    yield client
