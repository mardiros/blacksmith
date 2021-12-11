import pytest

from prometheus_client import REGISTRY, CollectorRegistry
from aiobreaker.state import CircuitBreakerError

from aioli import __version__
from aioli.domain.exceptions import HTTPError
from aioli.middleware.circuit_breaker import CircuitBreaker
from aioli.middleware.prometheus import PrometheusMetrics

from aioli.middleware.base import HTTPAddHeaderdMiddleware
from aioli.middleware.auth import HTTPAuthorization


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "middleware",
    [
        (HTTPAddHeaderdMiddleware, [{"foo": "bar"}], {"X-Req-Id": "42", "foo": "bar"}),
        (
            HTTPAuthorization,
            ["Bearer", "abc"],
            {"X-Req-Id": "42", "Authorization": "Bearer abc"},
        ),
    ],
)
async def test_headers_middleware(echo_middleware, middleware, dummy_http_request):
    middleware_cls, middleware_params, expected_headers = middleware
    auth = middleware_cls(*middleware_params)

    next = auth(echo_middleware)
    resp = await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

    assert resp.headers == expected_headers


@pytest.mark.asyncio
async def test_prom_default_registry(echo_middleware, dummy_http_request):
    metrics = PrometheusMetrics()
    next = metrics(echo_middleware)

    val = REGISTRY.get_sample_value("aioli_info", labels={"version": __version__})
    assert val == 1.0

    await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

    val = REGISTRY.get_sample_value(
        "aioli_request_latency_seconds_count",
        labels={
            "client_name": "dummy",
            "method": "GET",
            "path": "/dummies/{name}",
            "status_code": "200",
        },
    )
    assert val == 1


@pytest.mark.asyncio
async def test_prom_metrics(slow_middleware, dummy_http_request):
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    next = metrics(slow_middleware)

    val = registry.get_sample_value("aioli_info", labels={"version": __version__})
    assert val == 1.0

    val = registry.get_sample_value(
        "aioli_request_latency_seconds_bucket",
        labels={
            "le": "0.1",
            "client_name": "dummy",
            "method": "GET",
            "path": "/dummies/{name}",
            "status_code": "200",
        },
    )
    assert val is None

    await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

    val = registry.get_sample_value(
        "aioli_request_latency_seconds_count",
        labels={
            "client_name": "dummy",
            "method": "GET",
            "path": "/dummies/{name}",
            "status_code": "200",
        },
    )
    assert val == 1

    val = registry.get_sample_value(
        "aioli_request_latency_seconds_bucket",
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
        "aioli_request_latency_seconds_bucket",
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
        "aioli_request_latency_seconds_bucket",
        labels={
            "le": "3.2",
            "client_name": "dummy",
            "method": "GET",
            "path": "/dummies/{name}",
            "status_code": "200",
        },
    )
    assert val == 1.0


@pytest.mark.asyncio
async def test_prom_metrics_error(boom_middleware, dummy_http_request):
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    next = metrics(boom_middleware)

    with pytest.raises(HTTPError):
        await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

    val = registry.get_sample_value(
        "aioli_request_latency_seconds_bucket",
        labels={
            "le": "0.1",
            "client_name": "dummy",
            "method": "GET",
            "path": "/dummies/{name}",
            "status_code": "500",
        },
    )
    assert val == 1


@pytest.mark.asyncio
async def test_circuit_breaker(echo_middleware, boom_middleware, dummy_http_request):
    metrics = CircuitBreaker(fail_max=2)
    next = metrics(echo_middleware)
    resp = await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
    assert resp.status_code == 200

    next = metrics(boom_middleware)

    with pytest.raises(HTTPError) as exc:
        await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
    # with pytest.raises(HTTPError) as exc:
    #     await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

    with pytest.raises(CircuitBreakerError) as exc:
        await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
    assert exc.value.message == "Failures threshold reached, circuit breaker opened."

    # Event if it works, the circuit breaker is open
    next = metrics(echo_middleware)
    with pytest.raises(CircuitBreakerError) as exc:
        await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
