from typing import Any, Dict, List, Tuple

import pytest

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.typing import AsyncMiddleware
from blacksmith.middleware._async.http_caching import (
    AsyncAbstractCache,
    AsyncHTTPCachingMiddleware,
    CacheControlPolicy,
    get_max_age,
    get_vary_header_split,
    int_or_0,
)
from blacksmith.typing import HttpMethod


@pytest.mark.parametrize("params", [("0", 0), ("42", 42), ("2.5", 0), ("xxx", 0)])
def test_int_or_0(params: Tuple[str, int]):
    assert int_or_0(params[0]) == params[1]


@pytest.mark.parametrize(
    "params",
    [
        (HTTPResponse(200, {}, ""), 0),
        (
            HTTPResponse(
                200, {"age": "42", "cache-control": "max-age=142, public"}, ""
            ),
            100,
        ),
        (
            HTTPResponse(200, {"age": "0", "cache-control": "max-age=200, public"}, ""),
            200,
        ),
        (
            HTTPResponse(
                200, {"age": "42", "cache-control": "max-age=142, protected"}, ""
            ),
            0,
        ),
    ],
)
def test_get_max_age(params: Tuple[HTTPResponse, int]):
    assert get_max_age(params[0]) == params[1]


@pytest.mark.parametrize(
    "params",
    [
        (HTTPResponse(200, {}, ""), []),
        (HTTPResponse(200, {"vary": "Encoding"}, ""), ["encoding"]),
        (
            HTTPResponse(200, {"vary": "Encoding, X-Country-Code"}, ""),
            ["encoding", "x-country-code"],
        ),
    ],
)
def test_get_vary_header_split(params: Tuple[HTTPResponse, List[str]]):
    assert get_vary_header_split(params[0]) == params[1]


@pytest.mark.parametrize(
    "params",
    [
        ("GET", True),
        ("HEAD", False),
        ("POST", False),
        ("PUT", False),
        ("PATCH", False),
        ("DELETE", False),
        ("OPTIONS", False),
    ],
)
def test_policy_handle_request(params: Tuple[HttpMethod, bool]):
    policy = CacheControlPolicy("$")
    req = HTTPRequest("/")
    method, expected = params
    assert policy.handle_request(req, method, "", "") == expected


@pytest.mark.parametrize(
    "params",
    [
        ("dummies", "/", HTTPRequest("", {}, {}), "dummies$/"),
        ("bar", "/", HTTPRequest("", {}, {}), "bar$/"),
        (
            "dummies",
            "/names/{name}",
            HTTPRequest("", {"name": "dummy"}, {}),
            "dummies$/names/dummy",
        ),
        (
            "dummies",
            "/names",
            HTTPRequest("", {}, {"name": "dummy"}),
            "dummies$/names?name=dummy",
        ),
        (
            "dummies",
            "/names/{name}",
            HTTPRequest("", {"name": "dummy"}, {"foo": "bar"}),
            "dummies$/names/dummy?foo=bar",
        ),
        (
            "dummies",
            "/",
            HTTPRequest("", {}, {"foo": ["egg", "bar"]}),
            "dummies$/?foo=egg&foo=bar",
        ),
        (
            "dummies",
            "/",
            HTTPRequest("", {}, {"foo": ["e g", "bàr"]}),
            "dummies$/?foo=e+g&foo=b%C3%A0r",
        ),
        (
            "dummies",
            "/",
            HTTPRequest("", {}, {"foo": ["our$sep"]}),
            "dummies$/?foo=our%24sep",
        ),
    ],
)
def test_policy_get_vary_key(params: Tuple[str, str, HTTPRequest, str]):
    policy = CacheControlPolicy("$")
    assert policy.get_vary_key(params[0], params[1], params[2]) == params[3]


@pytest.mark.parametrize(
    "params",
    [
        (
            "dummies",
            "/",
            HTTPRequest("", headers={"Accept-Encoding": "gzip"}),
            [],
            "dummies$/$",
        ),
        (
            "dummies",
            "/",
            HTTPRequest("", headers={"Accept-Encoding": "gzip"}),
            ["Accept-Encoding"],
            "dummies$/$Accept-Encoding=gzip",
        ),
        (
            "dummies",
            "/",
            HTTPRequest("", headers={}),
            ["Accept-Encoding"],
            "dummies$/$Accept-Encoding=",
        ),
    ],
)
def test_policy_get_response_cache_key(
    params: Tuple[str, str, HTTPRequest, List[str], str]
):
    policy = CacheControlPolicy("$")
    assert (
        policy.get_response_cache_key(params[0], params[1], params[2], params[3])
        == f"{params[4]}"
    )


@pytest.mark.parametrize(
    "params",
    [
        ("dummies", "/", HTTPRequest(""), HTTPResponse(200, {}, ""), (0, "", [])),
        (
            "dummies",
            "/",
            HTTPRequest("", headers={"Cache-Control": "max-age=60, public"}),
            HTTPResponse(200, {"cache-control": "max-age=60, public"}, ""),
            (60, "dummies$/", []),
        ),
        (
            "dummies",
            "/",
            HTTPRequest("", headers={"Accept-Encoding": "gzip"}),
            HTTPResponse(
                200,
                {"vary": "Accept-Encoding", "cache-control": "max-age=60, public"},
                "",
            ),
            (60, "dummies$/", ["accept-encoding"]),
        ),
    ],
)
def test_policy_get_cache_info_for_response(
    params: Tuple[str, str, HTTPRequest, HTTPResponse, Tuple[int, str, List[str]]]
):
    policy = CacheControlPolicy("$")
    assert (
        policy.get_cache_info_for_response(params[0], params[1], params[2], params[3])
        == params[4]
    )


@pytest.mark.parametrize(
    "params",
    [
        {
            "path": "/",
            "request": HTTPRequest("", headers={}),
            "initial_cache": {},
            "expected_response_from_cache": None,
        },
        {
            "path": "/",
            "request": HTTPRequest("", headers={"x-country-code": "FR"}),
            "initial_cache": {
                "dummies$/": (42, '["x-country-code"]'),
            },
            "expected_response_from_cache": None,
        },
        {
            "path": "/",
            "request": HTTPRequest("", headers={"x-country-code": "FR"}),
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
async def test_get_from_cache(
    params: Dict[str, Any], fake_http_middleware_cache_with_data: AsyncAbstractCache
):
    middleware = AsyncHTTPCachingMiddleware(fake_http_middleware_cache_with_data)
    resp_from_cache = await middleware.get_from_cache(
        "dummies", params["path"], params["request"]
    )
    assert resp_from_cache == params["expected_response_from_cache"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "path": "/",
            "request": HTTPRequest("", {}, {}),
            "response": HTTPResponse(200, {}, ""),
            "expected_cache": {},
        },
        {
            "path": "/",
            "request": HTTPRequest("", {}, {}),
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
            "request": HTTPRequest("", headers={"x-country-code": "FR"}),
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
            "request": HTTPRequest("", headers={}),
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
            "request": HTTPRequest("", headers={"a": "A", "B": "B", "c": "C"}),
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
async def test_http_cache_response(
    params: Dict[str, Any], fake_http_middleware_cache: AsyncAbstractCache
):
    middleware = AsyncHTTPCachingMiddleware(fake_http_middleware_cache)

    resp_from_cache = await middleware.get_from_cache(
        "dummies", params["path"], params["request"]
    )
    await middleware.cache_response(
        "dummies", params["path"], params["request"], params["response"]
    )
    assert fake_http_middleware_cache.val == params["expected_cache"]  # type: ignore

    resp_from_cache = await middleware.get_from_cache(
        "dummies", params["path"], params["request"]
    )
    if params["expected_cache"]:
        assert resp_from_cache == params["response"]
    else:
        assert resp_from_cache is None


@pytest.mark.asyncio
async def test_cache_middleware(
    cachable_response: AsyncMiddleware,
    boom_middleware: AsyncMiddleware,
    fake_http_middleware_cache: AsyncAbstractCache,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):
    caching = AsyncHTTPCachingMiddleware(fake_http_middleware_cache)
    next = caching(cachable_response)
    resp = await next(
        dummy_http_request, "GET", "dummy", "/dummies/{name}", dummy_timeout
    )
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
    resp = await next(
        dummy_http_request, "GET", "dummy", "/dummies/{name}", dummy_timeout
    )
    assert resp == HTTPResponse(
        200, {"cache-control": "max-age=42, public"}, json="Cache Me"
    )


@pytest.mark.asyncio
async def test_cache_middleware_policy_handle(
    cachable_response: AsyncMiddleware,
    fake_http_middleware_cache: AsyncAbstractCache,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):
    class TrackHandleCacheControlPolicy(CacheControlPolicy):
        def __init__(self):
            super().__init__("%")
            self.handle_request_called = False

        def handle_request(self, req, method, client_name, path):  # type: ignore
            self.handle_request_called = True
            return False

    tracker = TrackHandleCacheControlPolicy()
    caching = AsyncHTTPCachingMiddleware(fake_http_middleware_cache, policy=tracker)
    next = caching(cachable_response)
    resp = await next(
        dummy_http_request, "GET", "dummy", "/dummies/{name}", dummy_timeout
    )
    assert tracker.handle_request_called is True
    assert fake_http_middleware_cache.val == {}  # type: ignore
    assert resp == HTTPResponse(
        200, {"cache-control": "max-age=42, public"}, json="Cache Me"
    )


@pytest.mark.asyncio
async def test_circuit_breaker_initialize(fake_http_middleware_cache: Any):
    caching = AsyncHTTPCachingMiddleware(fake_http_middleware_cache)
    await caching.initialize()
    assert fake_http_middleware_cache.initialize_called is True
