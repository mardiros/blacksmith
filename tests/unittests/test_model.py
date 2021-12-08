import json
from datetime import datetime
from typing import Optional

from aioli.domain.model import (
    CollectionParser,
    HeaderField,
    HTTPAuthentication,
    HTTPAuthorization,
    HTTPRequest,
    HTTPResponse,
    HTTPUnauthenticated,
    PathInfoField,
    PostBodyField,
    QueryStringField,
    Request,
    Response,
    parse_header_links,
)


def test_authotization_header():
    auth = HTTPAuthorization("Bearer", "abc")
    assert auth.headers == {"Authorization": "Bearer abc"}


def test_authotization_http_unauthenticated():
    auth = HTTPUnauthenticated()
    assert auth.headers == {}


def test_merge_middleware():
    req = HTTPRequest(
        "/",
        path={},
        querystring={},
        headers={"H": "h"},
        body="",
    )
    auth = HTTPAuthentication(headers={"X-Auth": "abc"})
    authreq = req.merge_middleware(auth)
    assert authreq.headers == {"H": "h", "X-Auth": "abc"}
    auth = HTTPAuthentication(headers={"X-Auth": "abcd"})
    authreq = req.merge_middleware(auth)
    assert authreq.headers == {"H": "h", "X-Auth": "abcd"}


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
