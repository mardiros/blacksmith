import pytest
from prometheus_client import CollectorRegistry  # type: ignore

from blacksmith.domain.model import HTTPRequest, HTTPTimeout
from blacksmith.domain.model.middleware.prometheus import PrometheusMetrics

from .scanned_resources import registry as resources_registry


@pytest.fixture
def registry():
    resources_registry.clients.clear()
    resources_registry.client_service.clear()
    yield resources_registry


@pytest.fixture
def dummy_http_request():
    return HTTPRequest(
        method="GET",
        url_pattern="/dummy/{name}",
        path={"name": 42},
        querystring={"foo": "bar"},
        headers={"X-Req-Id": "42"},
        body='{"bandi_manchot": "777"}',
    )


@pytest.fixture
def dummy_timeout():
    return HTTPTimeout()


@pytest.fixture
def prometheus_registry():
    return CollectorRegistry()


@pytest.fixture
def metrics(prometheus_registry: CollectorRegistry):
    return PrometheusMetrics(registry=prometheus_registry)
