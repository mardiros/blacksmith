from typing import Any

import pytest
from prometheus_client import CollectorRegistry  # type: ignore

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.model.middleware.http_cache import CacheControlPolicy
from blacksmith.domain.model.middleware.prometheus import PrometheusMetrics
from blacksmith.domain.typing import SyncMiddleware
from blacksmith.middleware._sync.http_cache import (
    SyncAbstractCache,
    SyncHTTPCacheMiddleware,
)


@pytest.mark.parametrize(
    "params",
    [
        {
            "path": "/",
            "request": HTTPRequest(method="GET", url_pattern="/", headers={}),
            "initial_cache": {},
            "expected_response_from_cache": None,
        },
        {
            "path": "/",
            "request": HTTPRequest(
                method="GET", url_pattern="/", headers={"x-country-code": "FR"}
            ),
            "initial_cache": {
                "dummies$/": (42, '["x-country-code"]'),
            },
            "expected_response_from_cache": None,
        },
        {
            "path": "/",
            "request": HTTPRequest(
                method="GET", url_pattern="/", headers={"x-country-code": "FR"}
            ),
            "initial_cache": {
                "dummies$/": (42, '["x-country-code"]'),
                "dummies$/$x-country-code=FR": (
                    42,
                    '{"status_code": 200, "headers": '
                    '{"cache-control": "max-age=42, public", "vary": '
                    '"X-Country-Code"}, "json": "En Francais"}',
                ),
            },
            "expected_response_from_cache": HTTPResponse(
                status_code=200,
                headers={
                    "cache-control": "max-age=42, public",
                    "vary": "X-Country-Code",
                },
                json="En Francais",
            ),
        },
    ],
)
def test_get_from_cache(
    params: dict[str, Any], fake_http_middleware_cache_with_data: SyncAbstractCache
) -> None:
    middleware = SyncHTTPCacheMiddleware(fake_http_middleware_cache_with_data)
    resp_from_cache = middleware.get_from_cache(
        "dummies", params["path"], params["request"]
    )
    assert resp_from_cache == params["expected_response_from_cache"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "path": "/",
            "request": HTTPRequest(method="GET", url_pattern="/"),
            "response": HTTPResponse(200, {}, ""),
            "expected_cachable": False,
            "expected_cache": {},
        },
        {
            "path": "/",
            "request": HTTPRequest(method="GET", url_pattern="/"),
            "response": HTTPResponse(200, {"cache-control": "max-age=42, public"}, ""),
            "expected_cachable": True,
            "expected_cache": {
                "dummies$/": (42, "[]"),
                "dummies$/$": (
                    42,
                    '{"status_code": 200, "headers": {"cache-control": "max-age=42, '
                    'public"}, "json": ""}',
                ),
            },
        },
        {
            "path": "/",
            "request": HTTPRequest(
                method="GET", url_pattern="/", headers={"x-country-code": "FR"}
            ),
            "response": HTTPResponse(
                200,
                {"cache-control": "max-age=42, public", "vary": "X-Country-Code"},
                "En Francais",
            ),
            "expected_cachable": True,
            "expected_cache": {
                "dummies$/": (42, '["x-country-code"]'),
                "dummies$/$x-country-code=FR": (
                    42,
                    '{"status_code": 200, "headers": '
                    '{"cache-control": "max-age=42, public", "vary": '
                    '"X-Country-Code"}, "json": "En Francais"}',
                ),
            },
        },
        {
            "path": "/",
            "request": HTTPRequest(method="GET", url_pattern="/"),
            "response": HTTPResponse(
                200,
                {"cache-control": "max-age=42, public", "vary": "X-Country-Code"},
                "missing_header",
            ),
            "expected_cachable": True,
            "expected_cache": {
                "dummies$/": (42, '["x-country-code"]'),
                "dummies$/$x-country-code=": (
                    42,
                    '{"status_code": 200, "headers": '
                    '{"cache-control": "max-age=42, public", "vary": '
                    '"X-Country-Code"}, "json": "missing_header"}',
                ),
            },
        },
        {
            "path": "/",
            "request": HTTPRequest(
                method="GET", url_pattern="/", headers={"a": "A", "B": "B", "c": "C"}
            ),
            "response": HTTPResponse(
                200,
                {"cache-control": "max-age=42, public", "vary": "a, b"},
                "many_headers",
            ),
            "expected_cachable": True,
            "expected_cache": {
                "dummies$/": (42, '["a", "b"]'),
                "dummies$/$a=A|b=B": (
                    42,
                    '{"status_code": 200, "headers": '
                    '{"cache-control": "max-age=42, public", "vary": '
                    '"a, b"}, "json": "many_headers"}',
                ),
            },
        },
    ],
)
def test_http_cache_response(
    params: dict[str, Any], fake_http_middleware_cache: SyncAbstractCache
) -> None:
    middleware = SyncHTTPCacheMiddleware(fake_http_middleware_cache)

    resp_from_cache = middleware.get_from_cache(
        "dummies", params["path"], params["request"]
    )
    resp = middleware.cache_response(
        "dummies", params["path"], params["request"], params["response"]
    )
    assert resp is params["expected_cachable"]
    assert fake_http_middleware_cache.val == params["expected_cache"]  # type: ignore

    resp_from_cache = middleware.get_from_cache(
        "dummies", params["path"], params["request"]
    )
    if params["expected_cache"]:
        assert resp_from_cache == params["response"]
    else:
        assert resp_from_cache is None


def test_cache_middleware(
    cachable_response: SyncMiddleware,
    boom_middleware: SyncMiddleware,
    fake_http_middleware_cache: SyncAbstractCache,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
) -> None:
    caching = SyncHTTPCacheMiddleware(fake_http_middleware_cache)
    next = caching(cachable_response)
    resp = next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert resp == HTTPResponse(
        200, {"cache-control": "max-age=42, public"}, json="Cache Me"
    )
    assert (
        fake_http_middleware_cache.val  # type: ignore
        == {
            "dummy$/dummies/42?foo=bar": (42, "[]"),
            "dummy$/dummies/42?foo=bar$": (
                42,
                '{"status_code": 200, "headers": '
                '{"cache-control": "max-age=42, public"}, '
                '"json": "Cache Me"}',
            ),
        }
    )

    # get from the cache, not from the boom which raises
    next = caching(boom_middleware)
    resp = next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert resp == HTTPResponse(
        200, {"cache-control": "max-age=42, public"}, json="Cache Me"
    )


def test_cache_middleware_policy_handle(
    cachable_response: SyncMiddleware,
    fake_http_middleware_cache: SyncAbstractCache,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
) -> None:
    class TrackHandleCacheControlPolicy(CacheControlPolicy):
        def __init__(self) -> None:
            super().__init__("%")
            self.handle_request_called = False

        def handle_request(self, req, client_name, path) -> bool:  # type: ignore
            self.handle_request_called = True
            return False

    tracker = TrackHandleCacheControlPolicy()
    caching = SyncHTTPCacheMiddleware(fake_http_middleware_cache, policy=tracker)
    next = caching(cachable_response)
    resp = next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert tracker.handle_request_called is True
    assert fake_http_middleware_cache.val == {}  # type: ignore
    assert resp == HTTPResponse(
        200, {"cache-control": "max-age=42, public"}, json="Cache Me"
    )


def test_cache_middleware_metrics_helpers(
    fake_http_middleware_cache: SyncAbstractCache,
    prometheus_registry: CollectorRegistry,
    metrics: PrometheusMetrics,
) -> None:
    caching = SyncHTTPCacheMiddleware(fake_http_middleware_cache, metrics)
    caching.inc_cache_miss("dummy", "cached", "GET", "/", 200)
    assert (
        prometheus_registry.get_sample_value(
            "blacksmith_cache_miss_total",
            labels={
                "client_name": "dummy",
                "cachable_state": "cached",
                "method": "GET",
                "path": "/",
                "status_code": "200",
            },
        )
        == 1
    )

    caching.observe_cache_hit("dummy", "GET", "/", 200, 0.07)
    assert (
        prometheus_registry.get_sample_value(
            "blacksmith_cache_hit_total",
            labels={
                "client_name": "dummy",
                "method": "GET",
                "path": "/",
                "status_code": "200",
            },
        )
        == 1
    )
    assert (
        prometheus_registry.get_sample_value(
            "blacksmith_cache_latency_seconds_bucket",
            labels={
                "client_name": "dummy",
                "method": "GET",
                "path": "/",
                "status_code": "200",
                "le": "0.04",
            },
        )
        == 0
    )
    assert (
        prometheus_registry.get_sample_value(
            "blacksmith_cache_latency_seconds_bucket",
            labels={
                "client_name": "dummy",
                "method": "GET",
                "path": "/",
                "status_code": "200",
                "le": "0.08",
            },
        )
        == 1
    )


def test_cache_middleware_metrics(
    cachable_response: SyncMiddleware,
    uncachable_response: SyncMiddleware,
    fake_http_middleware_cache: SyncAbstractCache,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
    prometheus_registry: CollectorRegistry,
    metrics: PrometheusMetrics,
) -> None:
    caching = SyncHTTPCacheMiddleware(fake_http_middleware_cache, metrics)
    next = caching(uncachable_response)
    next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert (
        prometheus_registry.get_sample_value(
            "blacksmith_cache_miss_total",
            labels={
                "client_name": "dummy",
                "cachable_state": "uncachable_response",
                "method": "GET",
                "path": "/dummies/{name}",
                "status_code": "200",
            },
        )
        == 1
    )

    next = caching(cachable_response)
    next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert (
        prometheus_registry.get_sample_value(
            "blacksmith_cache_miss_total",
            labels={
                "client_name": "dummy",
                "cachable_state": "cached",
                "method": "GET",
                "path": "/dummies/{name}",
                "status_code": "200",
            },
        )
        == 1
    )


def test_http_cache_initialize(fake_http_middleware_cache: Any) -> None:
    caching = SyncHTTPCacheMiddleware(fake_http_middleware_cache)
    caching.initialize()
    assert fake_http_middleware_cache.initialize_called is True
