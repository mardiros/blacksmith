import time
from datetime import timedelta

import prometheus_client
import pytest
from aiobreaker.state import CircuitBreakerError
from aiozipkin.helpers import Endpoint
from aiozipkin.sampler import Sampler
from aiozipkin.tracer import Tracer
from aiozipkin.transport import TransportABC
from prometheus_client import REGISTRY, CollectorRegistry

from blacksmith import __version__
from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse
from blacksmith.middleware.auth import HTTPAuthorization
from blacksmith.middleware.base import HTTPAddHeadersMiddleware, HTTPMiddleware
from blacksmith.middleware.circuit_breaker import CircuitBreaker, exclude_httpx_4xx
from blacksmith.middleware.prometheus import PrometheusMetrics
from blacksmith.middleware.zipkin import ZipkinMiddleware
from blacksmith.typing import ClientName, HttpMethod, Path


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
        (HTTPAddHeadersMiddleware, [{"foo": "bar"}], {"X-Req-Id": "42", "foo": "bar"}),
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

    val = REGISTRY.get_sample_value("blacksmith_info", labels={"version": __version__})
    assert val == 1.0

    await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

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


@pytest.mark.asyncio
async def test_prom_metrics(slow_middleware, dummy_http_request):
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    next = metrics(slow_middleware)

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

    await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

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


@pytest.mark.asyncio
async def test_prom_metrics_error(boom_middleware, dummy_http_request):
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    next = metrics(boom_middleware)

    with pytest.raises(HTTPError):
        await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

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


@pytest.mark.asyncio
async def test_circuit_breaker_prometheus_metrics(
    echo_middleware, invalid_middleware, boom_middleware, dummy_http_request
):
    OPEN = 2.0
    HALF_OPEN = 1.0
    CLOSED = 0.0
    registry = CollectorRegistry()
    prom = PrometheusMetrics(registry=registry)
    cbreaker = CircuitBreaker(
        fail_max=2,
        timeout_duration=timedelta(milliseconds=100),
        prometheus_metrics=prom,
    )
    echo_next = cbreaker(echo_middleware)
    invalid_next = cbreaker(invalid_middleware)
    boom_next = cbreaker(boom_middleware)
    with pytest.raises(HTTPError):
        await boom_next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
    with pytest.raises(CircuitBreakerError):
        await boom_next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

    registry.get_sample_value("blacksmith_circuit_breaker_error", labels=["dummy"]) == 1
    registry.get_sample_value(
        "blacksmith_circuit_breaker_state", labels=["dummy"]
    ) == OPEN

    with pytest.raises(CircuitBreakerError):
        await echo_next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
    registry.get_sample_value("blacksmith_circuit_breaker_error", labels=["dummy"]) == 2

    time.sleep(0.110)
    await echo_next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
    registry.get_sample_value("blacksmith_circuit_breaker_error", labels=["dummy"]) == 2
    registry.get_sample_value(
        "blacksmith_circuit_breaker_state", labels=["dummy"]
    ) == HALF_OPEN
    with pytest.raises(HTTPError):
        await invalid_next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
    registry.get_sample_value("blacksmith_circuit_breaker_error", labels=["dummy"]) == 2
    registry.get_sample_value(
        "blacksmith_circuit_breaker_state", labels=["dummy"]
    ) == HALF_OPEN

    time.sleep(0.110)
    next = cbreaker(echo_middleware)
    registry.get_sample_value("blacksmith_circuit_breaker_error", labels=["dummy"]) == 2
    registry.get_sample_value(
        "blacksmith_circuit_breaker_state", labels=["dummy"]
    ) == CLOSED


class Transport(TransportABC):
    def __init__(self):
        self.records = []

    def send(self, record) -> None:
        """Sends data to zipkin collector."""
        self.records.append(record.asdict())

    async def close(self) -> None:
        """Performs additional cleanup actions if required."""


@pytest.mark.asyncio
async def test_zipkin_middleware(echo_middleware, dummy_http_request):
    transport = Transport()
    tracer = Tracer(transport, Sampler(), Endpoint("srv", None, None, None))
    span = tracer.new_trace()
    middleware = ZipkinMiddleware(lambda: span, lambda: tracer)
    next = middleware(echo_middleware)
    await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

    assert transport.records == [
        {
            "annotations": [],
            "debug": False,
            "duration": transport.records[0]["duration"],
            "id": transport.records[0]["id"],
            "localEndpoint": {"serviceName": "srv"},
            "name": "GET /dummies/42",
            "parentId": span.context.span_id,
            "remoteEndpoint": None,
            "shared": False,
            "tags": {
                "blacksmith.client_name": "dummy",
                "http.path": "/dummies/{name}",
                "http.querystring": "{'foo': 'bar'}",
                "kind": "CLIENT",
            },
            "timestamp": transport.records[0]["timestamp"],
            "traceId": transport.records[0]["traceId"],
        },
    ]
