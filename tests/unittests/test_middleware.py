import prometheus_client
import pytest
from aiobreaker.state import CircuitBreakerError
from prometheus_client import REGISTRY, CollectorRegistry

from aioli import __version__
from aioli.domain.exceptions import HTTPError
from aioli.domain.model.http import HTTPRequest, HTTPResponse
from aioli.middleware.auth import HTTPAuthorization
from aioli.middleware.base import HTTPAddHeaderdMiddleware, HTTPMiddleware
from aioli.middleware.circuit_breaker import CircuitBreaker, exclude_httpx_4xx
from aioli.middleware.prometheus import PrometheusMetrics
from aioli.typing import ClientName, HttpMethod, Path


def test_authorization_header():
    auth = HTTPAuthorization("Bearer", "abc")
    assert auth.headers == {"Authorization": "Bearer abc"}


@pytest.mark.asyncio
@pytest.mark.parametrize("middleware", [HTTPMiddleware])
async def test_empty_middleware(middleware, dummy_http_request):
    auth = middleware()

    async def handle_req(
        req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
    ) -> HTTPResponse:
        return HTTPResponse(200, req.headers, json=req)

    next = auth(handle_req)
    resp = await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

    assert resp.headers == dummy_http_request.headers


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
    # reset the registry
    prometheus_client.REGISTRY = CollectorRegistry()


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


@pytest.mark.parametrize(
    "exc",
    [
        HTTPError("Mmm", HTTPRequest("/", {}, {}, {}), HTTPResponse(400, {}, {})),
        HTTPError("Mmm", HTTPRequest("/", {}, {}, {}), HTTPResponse(401, {}, {})),
        HTTPError("Mmm", HTTPRequest("/", {}, {}, {}), HTTPResponse(403, {}, {})),
        HTTPError("Mmm", HTTPRequest("/", {}, {}, {}), HTTPResponse(422, {}, {})),
    ],
)
def test_excluded_list(exc):
    assert exclude_httpx_4xx(exc) is True


@pytest.mark.parametrize(
    "exc",
    [
        RuntimeError("Boom"),
        ValueError("Boom"),
        HTTPError("Mmm", HTTPRequest("/", {}, {}, {}), HTTPResponse(500, {}, {})),
        HTTPError("Mmm", HTTPRequest("/", {}, {}, {}), HTTPResponse(503, {}, {})),
    ],
)
def test_included_list(exc):
    assert exclude_httpx_4xx(exc) is False


@pytest.mark.asyncio
async def test_circuit_breaker_5xx(
    echo_middleware, boom_middleware, dummy_http_request
):
    cbreaker = CircuitBreaker(fail_max=2)
    next = cbreaker(echo_middleware)
    resp = await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
    assert resp.status_code == 200

    next = cbreaker(boom_middleware)

    with pytest.raises(HTTPError) as exc:
        await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
    # with pytest.raises(HTTPError) as exc:
    #     await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

    with pytest.raises(CircuitBreakerError) as exc:
        await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
    assert exc.value.message == "Failures threshold reached, circuit breaker opened."

    # Event if it works, the circuit breaker is open
    next = cbreaker(echo_middleware)
    with pytest.raises(CircuitBreakerError) as exc:
        await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

    # Other service is still working
    resp = await next(dummy_http_request, "GET", "foo", "/dummies/{name}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_circuit_breaker_4xx(
    echo_middleware, invalid_middleware, dummy_http_request
):
    cbreaker = CircuitBreaker(fail_max=2)
    next = cbreaker(invalid_middleware)
    with pytest.raises(HTTPError) as exc:
        await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
    with pytest.raises(HTTPError) as exc:
        await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

    next = cbreaker(echo_middleware)
    # Other service is still working
    resp = await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
    assert resp.status_code == 200
