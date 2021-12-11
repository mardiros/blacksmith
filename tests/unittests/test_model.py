import json
from datetime import datetime
from typing import Optional, cast

import pytest

from aioli.domain.exceptions import NoResponseSchemaException
from aioli.domain.model import (
    CollectionIterator,
    CollectionParser,
    HeaderField,
    HTTPRequest,
    HTTPResponse,
    PathInfoField,
    PostBodyField,
    QueryStringField,
    Request,
    Response,
    ResponseBox,
)
from aioli.domain.model.http import HTTPTimeout, parse_header_links
from aioli.middleware.auth import HTTPAuthorization, HTTPUnauthenticated
from aioli.middleware.base import HTTPAddHeaderdMiddleware, HTTPMiddleware
from aioli.typing import ClientName, HttpMethod, Path


class GetResponse(Response):
    name: str
    age: int


def test_timeout_eq():
    assert HTTPTimeout() == HTTPTimeout()
    assert HTTPTimeout(10) == HTTPTimeout(10)
    assert HTTPTimeout(10, 20) == HTTPTimeout(10, 20)


def test_timeout_neq():
    assert HTTPTimeout() != HTTPTimeout(42)
    assert HTTPTimeout(42) != HTTPTimeout(42, 42)
    assert HTTPTimeout(42, 42) != HTTPTimeout(42, 43)


def test_authorization_header():
    auth = HTTPAuthorization("Bearer", "abc")
    assert auth.headers == {"Authorization": "Bearer abc"}


@pytest.mark.asyncio
@pytest.mark.parametrize("middleware", [HTTPMiddleware, HTTPUnauthenticated])
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
async def test_headers_middleware(middleware, dummy_http_request):
    middleware_cls, middleware_params, expected_headers = middleware
    auth = middleware_cls(*middleware_params)

    async def handle_req(
        req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
    ) -> HTTPResponse:
        return HTTPResponse(200, req.headers, json=req)

    next = auth(handle_req)
    resp = await next(dummy_http_request, "GET", "dummy", "/dummies/{name}")

    assert resp.headers == expected_headers


def test_request_url():
    req = HTTPRequest(
        "/foo/{name}/bar/{id}",
        path={"id": 42, "name": "John"},
        querystring={},
        headers={"H": "h"},
        body="",
    )

    assert req.url == "/foo/John/bar/42"


def test_param_to_req():
    class Dummy(Request):
        x_message_id: int = HeaderField(default=123, alias="X-Message-Id")
        x_sub_id: Optional[int] = HeaderField(alias="X-Sub-Id")
        name: str = PathInfoField()
        country: str = QueryStringField()
        state: Optional[str] = QueryStringField()
        age: int = PostBodyField()
        birthdate: datetime = PostBodyField()

    dummy = Dummy(name="Jane", country="FR", age=23, birthdate=datetime(1956, 12, 13))
    req = dummy.to_http_request("/dummies/{name}")
    assert req.url == "/dummies/Jane"
    assert req.headers == {"X-Message-Id": "123"}
    assert req.querystring == {"country": "FR"}
    assert json.loads(req.body) == {"age": 23, "birthdate": "1956-12-13T00:00:00"}


def test_response_from_http_response():
    class Dummy(Response):
        name: str

    resp = HTTPResponse(200, {}, {"name": "Jane", "age": 23})
    dummy = Dummy.from_http_response(resp)

    assert dummy == Dummy(name="Jane")


def test_parse_header_links():
    links = parse_header_links("")
    assert links == []
    links = parse_header_links(
        '<https://ne.xt/>; rel="next", <https://la.st/>; rel="last"'
    )
    assert links == [
        {"rel": "next", "url": "https://ne.xt/"},
        {"rel": "last", "url": "https://la.st/"},
    ]

    links = parse_header_links("<https://la.st/>")
    assert links == [{"url": "https://la.st/"}]


def test_collection_parser():
    resp = HTTPResponse(
        200,
        {
            "Total-Count": "20",
            "link": '<https://dummy/?page=2>; rel="next", <https://dummy/?page=4>; rel="last"',
        },
        [{"id": 1}, {"id": 1}],
    )
    resp = CollectionParser(resp)
    assert resp.meta.count == 2
    assert resp.meta.total_count == 20
    assert resp.meta.links == {
        "last": {"rel": "last", "url": "https://dummy/?page=4"},
        "next": {"rel": "next", "url": "https://dummy/?page=2"},
    }


def test_response_box():
    resp = ResponseBox(
        HTTPResponse(
            200,
            {},
            {
                "name": "Alice",
                "age": 24,
                "useless": True,
            },
        ),
        GetResponse,
        "",
        "",
        "",
        "",
    )
    assert resp.response.dict() == {"age": 24, "name": "Alice"}
    assert resp.json == {"age": 24, "name": "Alice", "useless": True}


def test_response_box_no_schema():
    resp = ResponseBox(
        HTTPResponse(
            200,
            {},
            {
                "name": "Alice",
                "age": 24,
                "useless": True,
            },
        ),
        None,
        "GET",
        "/dummies",
        "Dummy",
        "api",
    )
    with pytest.raises(NoResponseSchemaException) as ctx:
        assert resp.response
    assert (
        str(ctx.value)
        == "No response schema in route 'GET /dummies' in resource'Dummy' in client 'api'"
    )


def test_collection_iterator():
    collec = CollectionIterator(
        HTTPResponse(
            200,
            {"Total-Count": "5"},
            [
                {
                    "name": "Alice",
                    "age": 24,
                    "useless": True,
                },
                {
                    "name": "Bob",
                    "age": 42,
                },
            ],
        ),
        GetResponse,
        CollectionParser,
    )
    assert collec.meta.count == 2
    assert collec.meta.total_count == 5
    list_collec = list(collec)
    assert list_collec == [
        {
            "name": "Alice",
            "age": 24,
        },
        {
            "name": "Bob",
            "age": 42,
        },
    ]
