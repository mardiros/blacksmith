import json

import pytest
from blacksmith.middleware.http_caching import (
    HttpCachingMiddleware,
    get_vary_header_split,
    get_vary_key,
    int_or_0,
    get_max_age,
)
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse


@pytest.mark.parametrize("params", [("0", 0), ("42", 42), ("2.5", 0), ("xxx", 0)])
def test_int_or_0(params):
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
def test_get_max_age(params):
    assert get_max_age(params[0]) == params[1]


@pytest.mark.parametrize(
    "params",
    [
        ("/", HTTPRequest("", {}, {}), "/"),
        ("/names/{name}", HTTPRequest("", {"name": "dummy"}, {}), "/names/dummy"),
        ("/names", HTTPRequest("", {}, {"name": "dummy"}), "/names?name=dummy"),
        (
            "/names/{name}",
            HTTPRequest("", {"name": "dummy"}, {"foo": "bar"}),
            "/names/dummy?foo=bar",
        ),
        ("/", HTTPRequest("", {}, {"foo": ["egg", "bar"]}), "/?foo=egg&foo=bar"),
        ("/", HTTPRequest("", {}, {"foo": ["e g", "bàr"]}), "/?foo=e+g&foo=b%C3%A0r"),
        ("/", HTTPRequest("", {}, {"foo": ["our$sep"]}), "/?foo=our%24sep"),
    ],
)
def test_get_vary_key(params):
    assert get_vary_key(params[0], params[1]) == params[2]


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
def test_get_vary_header_split(params):
    assert get_vary_header_split(params[0]) == params[1]


@pytest.mark.parametrize(
    "params",
    [
        (
            "/",
            HTTPRequest("", {}, {}),
            HTTPResponse(200, {}, ""),
            {},
        ),
        (
            "/",
            HTTPRequest("", {}, {}),
            HTTPResponse(200, {"cache-control": "max-age=42, public"}, ""),
            {
                "/": (42, "[]"),
                "/${}": (
                    42,
                    '{"status_code": 200, "headers": {"cache-control": "max-age=42, '
                    'public"}, "json": ""}',
                ),
            },
        ),
        (
            "/",
            HTTPRequest("", headers={"x-country-code": "FR"}),
            HTTPResponse(
                200,
                {"cache-control": "max-age=42, public", "vary": "X-Country-Code"},
                "En Francais",
            ),
            {
                "/": (42, '["x-country-code"]'),
                '/${"x-country-code": "FR"}': (
                    42,
                    '{"status_code": 200, "headers": '
                    '{"cache-control": "max-age=42, public", "vary": '
                    '"X-Country-Code"}, "json": "En Francais"}',
                ),
            },
        ),
        (
            "/",
            HTTPRequest("", headers={}),
            HTTPResponse(
                200,
                {"cache-control": "max-age=42, public", "vary": "X-Country-Code"},
                "missing_header",
            ),
            {
                "/": (42, '["x-country-code"]'),
                '/${"x-country-code": ""}': (
                    42,
                    '{"status_code": 200, "headers": '
                    '{"cache-control": "max-age=42, public", "vary": '
                    '"X-Country-Code"}, "json": "missing_header"}',
                ),
            },
        ),
        (
            "/",
            HTTPRequest("", headers={"a": "A", "b": "B", "c": "C"}),
            HTTPResponse(
                200,
                {"cache-control": "max-age=42, public", "vary": "a, b"},
                "many_headers",
            ),
            {
                "/": (42, '["a", "b"]'),
                '/${"a": "A", "b": "B"}': (
                    42,
                    '{"status_code": 200, "headers": '
                    '{"cache-control": "max-age=42, public", "vary": '
                    '"a, b"}, "json": "many_headers"}',
                ),
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_http_caching(params, fake_http_middleware_cache):
    middleware = HttpCachingMiddleware(fake_http_middleware_cache)
    path, req, resp, expected = params
    await middleware.cache_response(path, req, resp)
    assert fake_http_middleware_cache.val == expected

    resp_from_cache = await middleware.get_from_cache(path, req)
    if expected:
        assert resp_from_cache == resp
    else:
        assert resp_from_cache is None


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
def test_handle_request(params, fake_http_middleware_cache):
    middleware = HttpCachingMiddleware(fake_http_middleware_cache)
    req = HTTPRequest("/")
    method, expected = params
    assert middleware.handle_request(req, method, "", "") == expected

@pytest.mark.asyncio
async def test_cache_middleware(cachable_response, boom_middleware, fake_http_middleware_cache, dummy_http_request):
    caching = HttpCachingMiddleware(fake_http_middleware_cache)
    next = caching(cachable_response)
    resp = await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
    assert resp == HTTPResponse(200, {"cache-control": "max-age=42, public"}, json="Cache Me")

    # get from the cache, not from the boom which raises
    next = caching(boom_middleware)
    resp = await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")
    assert resp == HTTPResponse(200, {"cache-control": "max-age=42, public"}, json="Cache Me")

