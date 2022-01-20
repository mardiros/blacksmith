from typing import List, Tuple

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
def test_policy_handle_request(params: Tuple[HTTPMethod, bool]):
    method, expected = params
    policy = CacheControlPolicy("$")
    req = HTTPRequest(method, "/")
    assert policy.handle_request(req, "", "") == expected


@pytest.mark.parametrize(
    "params",
    [
        ("dummies", "/", HTTPRequest("GET", "/", {}, {}), "dummies$/"),
        ("bar", "/", HTTPRequest("GET", "/", {}, {}), "bar$/"),
        (
            "dummies",
            "/names/{name}",
            HTTPRequest("GET", "/", {"name": "dummy"}, {}),
            "dummies$/names/dummy",
        ),
        (
            "dummies",
            "/names",
            HTTPRequest("GET", "/", {}, {"name": "dummy"}),
            "dummies$/names?name=dummy",
        ),
        (
            "dummies",
            "/names/{name}",
            HTTPRequest("GET", "/", {"name": "dummy"}, {"foo": "bar"}),
            "dummies$/names/dummy?foo=bar",
        ),
        (
            "dummies",
            "/",
            HTTPRequest("GET", "/", {}, {"foo": ["egg", "bar"]}),
            "dummies$/?foo=egg&foo=bar",
        ),
        (
            "dummies",
            "/",
            HTTPRequest("GET", "/", {}, {"foo": ["e g", "bàr"]}),
            "dummies$/?foo=e+g&foo=b%C3%A0r",
        ),
        (
            "dummies",
            "/",
            HTTPRequest("GET", "/", {}, {"foo": ["our$sep"]}),
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
            HTTPRequest("GET", "/", headers={"Accept-Encoding": "gzip"}),
            [],
            "dummies$/$",
        ),
        (
            "dummies",
            "/",
            HTTPRequest("GET", "/", headers={"Accept-Encoding": "gzip"}),
            ["Accept-Encoding"],
            "dummies$/$Accept-Encoding=gzip",
        ),
        (
            "dummies",
            "/",
            HTTPRequest("GET", "/", headers={}),
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
        (
            "dummies",
            "/",
            HTTPRequest("GET", ""),
            HTTPResponse(200, {}, ""),
            (0, "", []),
        ),
        (
            "dummies",
            "/",
            HTTPRequest("GET", "/", headers={"Cache-Control": "max-age=60, public"}),
            HTTPResponse(200, {"cache-control": "max-age=60, public"}, ""),
            (60, "dummies$/", []),
        ),
        (
            "dummies",
            "/",
            HTTPRequest("GET", "/", headers={"Accept-Encoding": "gzip"}),
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
