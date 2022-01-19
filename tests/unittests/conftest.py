import pytest

from blacksmith.domain.model import HTTPRequest, HTTPTimeout

from .scanned_resources import registry as resources_registry


@pytest.fixture
def registry():
    resources_registry.clients.clear()
    resources_registry.client_service.clear()
    yield resources_registry


@pytest.fixture
def dummy_http_request():
    return HTTPRequest(
        "GET",
        "/dummy/{name}",
        {"name": 42},
        {"foo": "bar"},
        {"X-Req-Id": "42"},
        '{"bandi_manchot": "777"}',
    )


@pytest.fixture
def dummy_timeout():
    return HTTPTimeout()
