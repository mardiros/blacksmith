import pytest

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse
from blacksmith.domain.model.middleware.http_cache import (
    CacheControlPolicy,
    get_max_age,
    get_vary_header_split,
    int_or_0,
)
from blacksmith.typing import HTTPMethod


@pytest.mark.parametrize("params", [("0", 0), ("42", 42), ("2.5", 0), ("xxx", 0)])
def test_int_or_0(params: tuple[str, int]):
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
def test_get_max_age(params: tuple[HTTPResponse, int]):
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
def test_get_vary_header_split(params: tuple[HTTPResponse, list[str]]):
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
def test_policy_handle_request(params: tuple[HTTPMethod, bool]):
    method, expected = params
    policy = CacheControlPolicy("$")
    req = HTTPRequest(method=method, url_pattern="/")
    assert policy.handle_request(req, "", "") == expected


@pytest.mark.parametrize(
    "params",
    [
        (
            "dummies",
            "/",
            HTTPRequest(method="GET", url_pattern="/", path={}, querystring={}),
            "dummies$/",
        ),
        (
            "bar",
            "/",
            HTTPRequest(method="GET", url_pattern="/", path={}, querystring={}),
            "bar$/",
        ),
        (
            "dummies",
            "/names/{name}",
            HTTPRequest(
                method="GET", url_pattern="/", path={"name": "dummy"}, querystring={}
            ),
            "dummies$/names/dummy",
        ),
        (
            "dummies",
            "/names",
            HTTPRequest(
                method="GET", url_pattern="/", path={}, querystring={"name": "dummy"}
            ),
            "dummies$/names?name=dummy",
        ),
        (
            "dummies",
            "/names/{name}",
            HTTPRequest(
                method="GET",
                url_pattern="/",
                path={"name": "dummy"},
                querystring={"foo": "bar"},
            ),
            "dummies$/names/dummy?foo=bar",
        ),
        (
            "dummies",
            "/",
            HTTPRequest(
                method="GET",
                url_pattern="/",
                path={},
                querystring={"foo": ["egg", "bar"]},
            ),
            "dummies$/?foo=egg&foo=bar",
        ),
        (
            "dummies",
            "/",
            HTTPRequest(
                method="GET",
                url_pattern="/",
                path={},
                querystring={"foo": ["e g", "bàr"]},
            ),
            "dummies$/?foo=e+g&foo=b%C3%A0r",
        ),
        (
            "dummies",
            "/",
            HTTPRequest(
                method="GET", url_pattern="/", path={}, querystring={"foo": ["our$sep"]}
            ),
            "dummies$/?foo=our%24sep",
        ),
    ],
)
def test_policy_get_vary_key(params: tuple[str, str, HTTPRequest, str]):
    policy = CacheControlPolicy("$")
    assert policy.get_vary_key(params[0], params[1], params[2]) == params[3]


@pytest.mark.parametrize(
    "params",
    [
        (
            "dummies",
            "/",
            HTTPRequest(
                method="GET", url_pattern="/", headers={"Accept-Encoding": "gzip"}
            ),
            [],
            "dummies$/$",
        ),
        (
            "dummies",
            "/",
            HTTPRequest(
                method="GET", url_pattern="/", headers={"Accept-Encoding": "gzip"}
            ),
            ["Accept-Encoding"],
            "dummies$/$Accept-Encoding=gzip",
        ),
        (
            "dummies",
            "/",
            HTTPRequest(method="GET", url_pattern="/", headers={}),
            ["Accept-Encoding"],
            "dummies$/$Accept-Encoding=",
        ),
    ],
)
def test_policy_get_response_cache_key(
    params: tuple[str, str, HTTPRequest, list[str], str],
):
    policy = CacheControlPolicy("$")
    assert (
        policy.get_response_cache_key(params[0], params[1], params[2], params[3])
        == f"{params[4]}"
    )


@pytest.mark.parametrize(
    "params",
    [
        (
            "dummies",
            "/",
            HTTPRequest(method="GET", url_pattern=""),
            HTTPResponse(200, {}, ""),
            (0, "", []),
        ),
        (
            "dummies",
            "/",
            HTTPRequest(
                method="GET",
                url_pattern="/",
                headers={"Cache-Control": "max-age=60, public"},
            ),
            HTTPResponse(200, {"cache-control": "max-age=60, public"}, ""),
            (60, "dummies$/", []),
        ),
        (
            "dummies",
            "/",
            HTTPRequest(
                method="GET", url_pattern="/", headers={"Accept-Encoding": "gzip"}
            ),
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
    params: tuple[str, str, HTTPRequest, HTTPResponse, tuple[int, str, list[str]]],
):
    policy = CacheControlPolicy("$")
    assert (
        policy.get_cache_info_for_response(params[0], params[1], params[2], params[3])
        == params[4]
    )
