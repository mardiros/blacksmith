from typing import Any, Dict

import pytest

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.model.middleware.http_cache import CacheControlPolicy
from blacksmith.domain.typing import SyncMiddleware
from blacksmith.middleware._sync.http_caching import (
    SyncAbstractCache,
    SyncHTTPCachingMiddleware,
)


@pytest.mark.parametrize(
    "params",
    [
        {
            "path": "/",
            "request": HTTPRequest("GET", "/", headers={}),
            "initial_cache": {},
            "expected_response_from_cache": None,
        },
        {
            "path": "/",
            "request": HTTPRequest("GET", "/", headers={"x-country-code": "FR"}),
            "initial_cache": {
                "dummies$/": (42, '["x-country-code"]'),
            },
            "expected_response_from_cache": None,
        },
        {
            "path": "/",
            "request": HTTPRequest("GET", "/", headers={"x-country-code": "FR"}),
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
@pytest.mark.asyncio
def test_get_from_cache(
    params: Dict[str, Any], fake_http_middleware_cache_with_data: SyncAbstractCache
):
    middleware = SyncHTTPCachingMiddleware(fake_http_middleware_cache_with_data)
    resp_from_cache = middleware.get_from_cache(
        "dummies", params["path"], params["request"]
    )
    assert resp_from_cache == params["expected_response_from_cache"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "path": "/",
            "request": HTTPRequest("GET", "/", {}, {}),
            "response": HTTPResponse(200, {}, ""),
            "expected_cache": {},
        },
        {
            "path": "/",
            "request": HTTPRequest("GET", "/", {}, {}),
            "response": HTTPResponse(200, {"cache-control": "max-age=42, public"}, ""),
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
            "request": HTTPRequest("GET", "/", headers={"x-country-code": "FR"}),
            "response": HTTPResponse(
                200,
                {"cache-control": "max-age=42, public", "vary": "X-Country-Code"},
                "En Francais",
            ),
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
            "request": HTTPRequest("GET", "/", headers={}),
            "response": HTTPResponse(
                200,
                {"cache-control": "max-age=42, public", "vary": "X-Country-Code"},
                "missing_header",
            ),
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
            "request": HTTPRequest("GET", "/", headers={"a": "A", "B": "B", "c": "C"}),
            "response": HTTPResponse(
                200,
                {"cache-control": "max-age=42, public", "vary": "a, b"},
                "many_headers",
            ),
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
@pytest.mark.asyncio
def test_http_cache_response(
    params: Dict[str, Any], fake_http_middleware_cache: SyncAbstractCache
):
    middleware = SyncHTTPCachingMiddleware(fake_http_middleware_cache)

    resp_from_cache = middleware.get_from_cache(
        "dummies", params["path"], params["request"]
    )
    middleware.cache_response(
        "dummies", params["path"], params["request"], params["response"]
    )
    assert fake_http_middleware_cache.val == params["expected_cache"]  # type: ignore

    resp_from_cache = middleware.get_from_cache(
        "dummies", params["path"], params["request"]
    )
    if params["expected_cache"]:
        assert resp_from_cache == params["response"]
    else:
        assert resp_from_cache is None


@pytest.mark.asyncio
def test_cache_middleware(
    cachable_response: SyncMiddleware,
    boom_middleware: SyncMiddleware,
    fake_http_middleware_cache: SyncAbstractCache,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):
    caching = SyncHTTPCachingMiddleware(fake_http_middleware_cache)
    next = caching(cachable_response)
    resp = next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert resp == HTTPResponse(
        200, {"cache-control": "max-age=42, public"}, json="Cache Me"
    )
    assert fake_http_middleware_cache.val == {  # type: ignore
        "dummy$/dummies/42?foo=bar": (42, "[]"),
        "dummy$/dummies/42?foo=bar$": (
            42,
            '{"status_code": 200, "headers": '
            '{"cache-control": "max-age=42, public"}, '
            '"json": "Cache Me"}',
        ),
    }

    # get from the cache, not from the boom which raises
    next = caching(boom_middleware)
    resp = next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert resp == HTTPResponse(
        200, {"cache-control": "max-age=42, public"}, json="Cache Me"
    )


@pytest.mark.asyncio
def test_cache_middleware_policy_handle(
    cachable_response: SyncMiddleware,
    fake_http_middleware_cache: SyncAbstractCache,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):
    class TrackHandleCacheControlPolicy(CacheControlPolicy):
        def __init__(self):
            super().__init__("%")
            self.handle_request_called = False

        def handle_request(self, req, client_name, path):  # type: ignore
            self.handle_request_called = True
            return False

    tracker = TrackHandleCacheControlPolicy()
    caching = SyncHTTPCachingMiddleware(fake_http_middleware_cache, policy=tracker)
    next = caching(cachable_response)
    resp = next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert tracker.handle_request_called is True
    assert fake_http_middleware_cache.val == {}  # type: ignore
    assert resp == HTTPResponse(
        200, {"cache-control": "max-age=42, public"}, json="Cache Me"
    )


@pytest.mark.asyncio
def test_circuit_breaker_initialize(fake_http_middleware_cache: Any):
    caching = SyncHTTPCachingMiddleware(fake_http_middleware_cache)
    caching.initialize()
    assert fake_http_middleware_cache.initialize_called is True
