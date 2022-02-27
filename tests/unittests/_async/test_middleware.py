from typing import Any, Dict, cast

import prometheus_client
import pytest
from prometheus_client import REGISTRY, CollectorRegistry
from purgatory.domain.messages import Event
from purgatory.domain.messages.events import (
    CircuitBreakerCreated,
    CircuitBreakerFailed,
    CircuitBreakerRecovered,
    ContextChanged,
)
from purgatory.domain.model import OpenedState
from purgatory.service._async.circuitbreaker import AsyncCircuitBreakerFactory

from blacksmith import __version__
from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.model.middleware.circuit_breaker import exclude_httpx_4xx
from blacksmith.domain.model.middleware.prometheus import PrometheusMetrics
from blacksmith.domain.typing import AsyncMiddleware
from blacksmith.middleware._async.auth import AsyncHTTPAuthorizationMiddleware
from blacksmith.middleware._async.base import (
    AsyncHTTPAddHeadersMiddleware,
    AsyncHTTPMiddleware,
)
from blacksmith.middleware._async.circuit_breaker import AsyncCircuitBreakerMiddleware
from blacksmith.middleware._async.prometheus import AsyncPrometheusMiddleware
from blacksmith.middleware._async.zipkin import AsyncZipkinMiddleware
from tests.unittests.time import AsyncSleep


def test_authorization_header():
    auth = AsyncHTTPAuthorizationMiddleware("Bearer", "abc")
    assert auth.headers == {"Authorization": "Bearer abc"}


async def test_empty_middleware(
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
    echo_middleware: AsyncMiddleware,
):
    auth = AsyncHTTPMiddleware()

    next = auth(echo_middleware)
    resp = await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert resp.headers == dummy_http_request.headers


@pytest.mark.parametrize(
    "params",
    [
        {
            "middleware_cls": AsyncHTTPAddHeadersMiddleware,
            "middleware_params": [{"foo": "bar"}],
            "expected_headers": {"X-Req-Id": "42", "foo": "bar"},
        },
        {
            "middleware_cls": AsyncHTTPAuthorizationMiddleware,
            "middleware_params": ["Bearer", "abc"],
            "expected_headers": {"X-Req-Id": "42", "Authorization": "Bearer abc"},
        },
    ],
)
async def test_headers_middleware(
    params: Dict[str, Any],
    echo_middleware: AsyncMiddleware,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):
    auth = params["middleware_cls"](*params["middleware_params"])

    next = auth(echo_middleware)
    resp = await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)

    assert resp.headers == params["expected_headers"]


async def test_prom_default_registry(
    echo_middleware: AsyncMiddleware,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):
    metrics = AsyncPrometheusMiddleware()
    next = metrics(echo_middleware)

    val = REGISTRY.get_sample_value("blacksmith_info", labels={"version": __version__})
    assert val == 1.0

    await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)

    val = REGISTRY.get_sample_value(
        "blacksmith_request_latency_seconds_count",
        labels={
            "client_name": "dummy",
            "method": "GET",
            "path": "/dummies/{name}",
            "status_code": "200",
        },
    )
    assert val == 1
    # reset the registry
    prometheus_client.REGISTRY = CollectorRegistry()


async def test_prom_metrics(
    slow_middleware: AsyncMiddleware,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    metrics_middleware = AsyncPrometheusMiddleware(metrics=metrics)
    next = metrics_middleware(slow_middleware)

    val = registry.get_sample_value("blacksmith_info", labels={"version": __version__})
    assert val == 1.0

    val = registry.get_sample_value(
        "blacksmith_request_latency_seconds_bucket",
        labels={
            "le": "0.1",
            "client_name": "dummy",
            "method": "GET",
            "path": "/dummies/{name}",
            "status_code": "200",
        },
    )
    assert val is None

    await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)

    val = registry.get_sample_value(
        "blacksmith_request_latency_seconds_count",
        labels={
            "client_name": "dummy",
            "method": "GET",
            "path": "/dummies/{name}",
            "status_code": "200",
        },
    )
    assert val == 1

    val = registry.get_sample_value(
        "blacksmith_request_latency_seconds_bucket",
        labels={
            "le": "0.05",
            "client_name": "dummy",
            "method": "GET",
            "path": "/dummies/{name}",
            "status_code": "200",
        },
    )
    assert val == 0.0

    val = registry.get_sample_value(
        "blacksmith_request_latency_seconds_bucket",
        labels={
            "le": "0.1",
            "client_name": "dummy",
            "method": "GET",
            "path": "/dummies/{name}",
            "status_code": "200",
        },
    )
    assert val == 1.0

    val = registry.get_sample_value(
        "blacksmith_request_latency_seconds_bucket",
        labels={
            "le": "3.2",
            "client_name": "dummy",
            "method": "GET",
            "path": "/dummies/{name}",
            "status_code": "200",
        },
    )
    assert val == 1.0


async def test_prom_metrics_error(
    boom_middleware: AsyncMiddleware,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    metrics_middleware = AsyncPrometheusMiddleware(metrics=metrics)
    next = metrics_middleware(boom_middleware)

    with pytest.raises(HTTPError):
        await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)

    val = registry.get_sample_value(
        "blacksmith_request_latency_seconds_bucket",
        labels={
            "le": "0.1",
            "client_name": "dummy",
            "method": "GET",
            "path": "/dummies/{name}",
            "status_code": "500",
        },
    )
    assert val == 1


@pytest.mark.parametrize(
    "exc",
    [
        HTTPError(
            "Mmm", HTTPRequest("GET", "/", {}, {}, {}), HTTPResponse(400, {}, {})
        ),
        HTTPError(
            "Mmm", HTTPRequest("GET", "/", {}, {}, {}), HTTPResponse(401, {}, {})
        ),
        HTTPError(
            "Mmm", HTTPRequest("GET", "/", {}, {}, {}), HTTPResponse(403, {}, {})
        ),
        HTTPError(
            "Mmm", HTTPRequest("GET", "/", {}, {}, {}), HTTPResponse(422, {}, {})
        ),
    ],
)
def test_excluded_list(exc: HTTPError):
    assert exclude_httpx_4xx(exc) is True


@pytest.mark.parametrize(
    "exc",
    [
        HTTPError(
            "Mmm", HTTPRequest("GET", "/", {}, {}, {}), HTTPResponse(500, {}, {})
        ),
        HTTPError(
            "Mmm", HTTPRequest("GET", "/", {}, {}, {}), HTTPResponse(503, {}, {})
        ),
    ],
)
def test_included_list(exc: HTTPError):
    assert exclude_httpx_4xx(exc) is False


async def test_circuit_breaker_5xx(
    echo_middleware: AsyncMiddleware,
    boom_middleware: AsyncMiddleware,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):
    cbreaker = AsyncCircuitBreakerMiddleware(threshold=2)
    next = cbreaker(echo_middleware)
    resp = await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert resp.status_code == 200

    next = cbreaker(boom_middleware)

    with pytest.raises(HTTPError):
        await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    with pytest.raises(HTTPError):
        await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)

    with pytest.raises(OpenedState) as exc:
        await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert str(exc.value) == "Circuit dummy is open"

    # Event if it works, the circuit breaker is open
    next = cbreaker(echo_middleware)
    with pytest.raises(OpenedState):
        await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)

    # Other service is still working
    resp = await next(dummy_http_request, "foo", "/dummies/{name}", dummy_timeout)
    assert resp.status_code == 200


async def test_circuit_breaker_4xx(
    echo_middleware: AsyncMiddleware,
    invalid_middleware: AsyncMiddleware,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):
    cbreaker = AsyncCircuitBreakerMiddleware(threshold=2)
    next = cbreaker(invalid_middleware)
    with pytest.raises(HTTPError):
        await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    with pytest.raises(HTTPError):
        await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)

    next = cbreaker(echo_middleware)
    # Other service is still working
    resp = await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert resp.status_code == 200


async def test_circuit_breaker_prometheus_metrics(
    echo_middleware: AsyncMiddleware,
    invalid_middleware: AsyncMiddleware,
    boom_middleware: AsyncMiddleware,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
    prometheus_registry: CollectorRegistry,
    metrics: PrometheusMetrics,
):
    OPEN = 2.0
    CLOSED = 0.0
    cbreaker = AsyncCircuitBreakerMiddleware(
        threshold=2,
        ttl=0.100,
        metrics=metrics,
    )
    echo_next = cbreaker(echo_middleware)
    invalid_next = cbreaker(invalid_middleware)
    boom_next = cbreaker(boom_middleware)

    with pytest.raises(HTTPError):
        await boom_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    with pytest.raises(HTTPError):
        await invalid_next(
            dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout
        )

    assert (
        prometheus_registry.get_sample_value(
            "blacksmith_circuit_breaker_error_total", labels={"client_name": "dummy"}
        )
        == 1
    )

    with pytest.raises(HTTPError):
        await boom_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    with pytest.raises(HTTPError):
        await boom_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    with pytest.raises(OpenedState):
        await boom_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)

    assert (
        prometheus_registry.get_sample_value(
            "blacksmith_circuit_breaker_error_total", labels={"client_name": "dummy"}
        )
        == 3
    )
    assert (
        prometheus_registry.get_sample_value(
            "blacksmith_circuit_breaker_state", labels={"client_name": "dummy"}
        )
        == OPEN
    )

    with pytest.raises(OpenedState):
        await echo_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)

    assert (
        prometheus_registry.get_sample_value(
            "blacksmith_circuit_breaker_error_total", labels={"client_name": "dummy"}
        )
        == 3
    )

    await AsyncSleep(0.110)
    await echo_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert (
        prometheus_registry.get_sample_value(
            "blacksmith_circuit_breaker_error_total", labels={"client_name": "dummy"}
        )
        == 3
    )
    assert (
        prometheus_registry.get_sample_value(
            "blacksmith_circuit_breaker_state", labels={"client_name": "dummy"}
        )
        == CLOSED
    )


async def test_circuit_breaker_initialize():
    class MockPurgatory:
        def __init__(self):
            self.called = False

        async def initialize(self):
            self.called = True

    cbreaker = AsyncCircuitBreakerMiddleware()
    purgatory_cb = MockPurgatory()
    cbreaker.circuit_breaker = cast(AsyncCircuitBreakerFactory, purgatory_cb)
    await cbreaker.initialize()
    assert purgatory_cb.called is True


async def test_circuit_breaker_listener(
    echo_middleware: AsyncMiddleware,
    boom_middleware: AsyncMiddleware,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):

    evts = []

    def hook(name: str, evt_name: str, evt: Event):
        evts.append((name, evt_name, evt))

    cbreaker = AsyncCircuitBreakerMiddleware(threshold=2, ttl=0.100, listeners=[hook])
    echo_next = cbreaker(echo_middleware)
    await echo_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert evts == [
        (
            "dummy",
            "circuit_breaker_created",
            CircuitBreakerCreated(name="dummy", threshold=2, ttl=0.1),
        )
    ]
    evts.clear()
    boom_next = cbreaker(boom_middleware)
    with pytest.raises(HTTPError):
        await boom_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    with pytest.raises(HTTPError):
        await boom_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    with pytest.raises(OpenedState):
        await boom_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)

    brk = await cbreaker.circuit_breaker.get_breaker("dummy")
    assert evts == [
        ("dummy", "failed", CircuitBreakerFailed(name="dummy", failure_count=1)),
        ("dummy", "failed", CircuitBreakerFailed(name="dummy", failure_count=2)),
        (
            "dummy",
            "state_changed",
            ContextChanged(
                name="dummy",
                state="opened",
                opened_at=brk.context._state.opened_at,  # type:ignore
            ),
        ),
    ]
    evts.clear()
    await AsyncSleep(0.110)
    await echo_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert evts == [
        (
            "dummy",
            "state_changed",
            ContextChanged(name="dummy", state="half-opened", opened_at=None),
        ),
        ("dummy", "recovered", CircuitBreakerRecovered(name="dummy")),
        (
            "dummy",
            "state_changed",
            ContextChanged(name="dummy", state="closed", opened_at=None),
        ),
    ]


async def test_zipkin_middleware(
    echo_middleware: AsyncMiddleware,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
    trace: Any,
):

    middleware = AsyncZipkinMiddleware(trace)
    next = middleware(echo_middleware)
    await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert trace.name == "GET /dummies/42"
    assert trace.kind == "CLIENT"
    assert trace.tags == {
        "blacksmith.client_name": "dummy",
        "http.path": "/dummies/{name}",
        "http.querystring": "{'foo': 'bar'}",
        "http.status_code": "200",
    }


async def test_zipkin_middleware_tag_error(
    boom_middleware: AsyncMiddleware,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
    trace: Any,
):

    middleware = AsyncZipkinMiddleware(trace)
    next = middleware(boom_middleware)
    with pytest.raises(HTTPError):
        await next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert trace.name == "GET /dummies/42"
    assert trace.kind == "CLIENT"
    assert trace.tags == {
        "blacksmith.client_name": "dummy",
        "http.path": "/dummies/{name}",
        "http.querystring": "{'foo': 'bar'}",
        "http.status_code": "500",
        "error": "true",
    }
