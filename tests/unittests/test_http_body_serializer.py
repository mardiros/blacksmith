import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, Optional, Union

import pytest
from pydantic import BaseModel, Field, HttpUrl, SecretStr

from blacksmith import (
    Attachment,
    HeaderField,
    HTTPRequest,
    PathInfoField,
    PostBodyField,
    QueryStringField,
    Request,
)
from blacksmith.domain.exceptions import UnregisteredContentTypeException
from blacksmith.domain.model.http import HTTPRawResponse, HTTPResponse
from blacksmith.domain.model.params import BODY, QUERY, AttachmentField
from blacksmith.service.http_body_serializer import (
    AbstractHttpBodySerializer,
    JSONEncoder,
    JsonRequestSerializer,
    UrlencodedRequestSerializer,
    get_location,
    register_http_body_serializer,
    serialize_part,
    serialize_request,
    serialize_request_body,
    serialize_response,
    unregister_http_body_serializer,
)
from blacksmith.typing import Json


class GetRequest(Request): ...


class DummyGetRequest(Request):
    secret: SecretStr = HeaderField()
    bar: int = QueryStringField()
    name: str = PathInfoField()


class DummyPostRequest(DummyGetRequest):
    foo: str = PostBodyField()


class DummyPostRequestTypes(Request):
    url: HttpUrl = PostBodyField()


class DummyAliasRequestTypes(Request):
    for_: str = QueryStringField(alias="for")


class DummyAttachement(Request):
    foo: str = PostBodyField()
    bar: Attachment = AttachmentField()


class DummyComplex(BaseModel):
    name: str


class DummyComplexAttachement(Request):
    foo: DummyComplex = PostBodyField()
    bar: Attachment = AttachmentField()


class DummyHTTPRepsonse(HTTPRawResponse):
    status_code: int
    headers: Mapping[str, str]

    def __init__(self, status_code: int, headers: Mapping[str, str], content: str):
        self.status_code = status_code
        self.headers = headers
        self._content = content

    @property
    def content(self) -> bytes:
        return self._content.encode(self.encoding)

    @property
    def text(self) -> str:
        return self._content

    @property
    def encoding(self) -> str:
        return "utf-8"


class MySerializer(AbstractHttpBodySerializer):
    def accept(self, content_type: str) -> bool:
        return content_type == "text/xml"

    def serialize(self, body: Union[dict[str, Any], Sequence[Any]]) -> str:
        return "<foo/>"

    def deserialize(self, body: bytes, encoding: Optional[str]) -> Json:
        return {"foo": "bar"}


class DummyPostRequestXML(Request):
    foo: str = PostBodyField()
    content_type: str = HeaderField(default="text/xml", alias="Content-Type")


def test_json_encoder() -> None:
    assert (
        json.dumps({"date": datetime(2020, 10, 5)}, cls=JSONEncoder)
        == '{"date": "2020-10-05T00:00:00"}'
    )

    with pytest.raises(TypeError) as ctx:
        json.dumps({"oops": object()}, cls=JSONEncoder)
    assert str(ctx.value) == "Object of type object is not JSON serializable"


def test_get_location_from_pydantic_v2() -> None:
    class Dummy(BaseModel):
        field: str = PostBodyField(default=None)

    assert get_location(Dummy.model_fields["field"]) == BODY


def test_get_location_raises_type_error_if_no_json_schema_extra() -> None:
    class Dummy(BaseModel):
        field: str = Field(default=None)

    with pytest.raises(TypeError) as ctx:
        get_location(Dummy.model_fields["field"])
    assert (
        str(ctx.value)
        == "not a PathInfoField | HeaderField | QueryStringField | PostBodyField"
    )


def test_get_location_raises_type_error_if_no_location() -> None:
    class Dummy(BaseModel):
        field: str = Field(default=None, json_schema_extra={"foo": "bar"})

    with pytest.raises(TypeError) as ctx:
        get_location(Dummy.model_fields["field"])
    assert (
        str(ctx.value)
        == "not a PathInfoField | HeaderField | QueryStringField | PostBodyField"
    )


def test_get_location_raises_type_error_if_callable() -> None:
    def my_json_schema_extra(s: Any):
        return s

    class Dummy(BaseModel):
        field: str = Field(default=None, json_schema_extra=my_json_schema_extra)

    with pytest.raises(TypeError) as ctx:
        get_location(Dummy.model_fields["field"])
    assert (
        str(ctx.value)
        == "not a PathInfoField | HeaderField | QueryStringField | PostBodyField"
    )


def test_serialize_part() -> None:
    class Dummy(Request):
        x_message_id: int = HeaderField(default=123, alias="X-Message-Id")
        name: str = PostBodyField()
        age: int = PostBodyField(default=10)
        city: Optional[str] = PostBodyField(None)
        state: Optional[str] = PostBodyField(None)
        country: str = PostBodyField()

    dummy = Dummy(name="Jane", country="FR", city="Saint Palais s/mer", state=None)
    obj = serialize_part(
        dummy,
        {
            "name": ...,
            "age": ...,
            "city": ...,
            "state": ...,
            "country": ...,
        },
        "body",
    )
    assert obj == {
        "name": "Jane",
        "age": 10,
        "city": "Saint Palais s/mer",
        "state": None,
        "country": "FR",
    }


def test_serialize_nested_dict() -> None:
    class Dummy(Request):
        type: str = PostBodyField()
        params: dict[str, Any] = PostBodyField()

    dummy = Dummy(type="bar", params={"a": "A", "b": 1})
    obj = serialize_part(dummy, {"type": "bar", "params": {"a": "A", "b": 1}}, "body")
    assert obj == {"type": "bar", "params": {"a": "A", "b": 1}}


def test_serialize_query_string() -> None:
    class Dummy(Request):
        type: list[str] = QueryStringField()

    dummy = Dummy(type=["foo", "bar"])
    obj = serialize_part(dummy, {"type": ...}, QUERY)
    assert obj == {"type": ["foo", "bar"]}


def test_serialize_nested_dict_attached() -> None:
    class Dummy(Request):
        type: str = PostBodyField()
        params: dict[str, Any] = PostBodyField()

    dummy = Dummy(type="bar", params={"a": "A", "b": 1})
    obj = serialize_part(
        dummy, {"type": "bar", "params": {"a": "A", "b": 1}}, "attachment"
    )
    assert obj == {"type": "bar", "params": '{"a": "A", "b": 1}'}


def test_serialize_part_default_with_none() -> None:
    class Dummy(Request):
        name: str = PostBodyField()
        age: Optional[int] = PostBodyField(default=10)

    dummy = Dummy(name="Jane", age=None)
    obj = serialize_part(
        dummy,
        {
            "name": ...,
            "age": ...,
            "created_at": ...,
        },
        "body",
    )
    assert obj == {
        "name": "Jane",
        "age": None,
    }


@pytest.mark.parametrize(
    "params",
    [
        pytest.param(
            {
                "req": GetRequest(),
                "body": {},
                "content_type": None,
                "expected": "",
            },
            id="empty",
        ),
        pytest.param(
            {
                "req": GetRequest(),
                "body": {},
                "content_type": "application/json",
                "expected": "{}",
            },
            id="empty",
        ),
        pytest.param(
            {
                "req": DummyPostRequest(
                    secret=SecretStr("yolo"), bar=1, name="jon", foo="bar"
                ),
                "body": {"foo"},
                "content_type": None,
                "expected": '{"foo": "bar"}',
            },
            id="body, default content-type is json",
        ),
        pytest.param(
            {
                "req": DummyPostRequest(
                    secret=SecretStr("yolo"), bar=1, name="jon", foo="bar"
                ),
                "body": {"foo"},
                "content_type": "application/json",
                "expected": '{"foo": "bar"}',
            },
            id="body with json",
        ),
    ],
)
def test_serialize_request_body(params: Mapping[str, Any]):
    body = serialize_request_body(params["req"], params["body"], params["content_type"])
    assert body == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        pytest.param(
            {
                "req": DummyPostRequestTypes(url=HttpUrl("http://mardiros.github.io")),
                "body": {"url"},
                "content_type": "application/json",
                "expected": '{"url": "http://mardiros.github.io/"}',
            },
            id="bared url",
        ),
        pytest.param(
            {
                "req": DummyPostRequestTypes(
                    url=HttpUrl("https://mardiros.github.io/blacksmith")
                ),
                "body": {"url"},
                "content_type": "application/json",
                "expected": '{"url": "https://mardiros.github.io/blacksmith"}',
            },
            id="url type with path",
        ),
    ],
)
def test_serialize_request_body_pydantic_2(params: Mapping[str, Any]):
    body = serialize_request_body(params["req"], params["body"], params["content_type"])
    assert body == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        pytest.param(
            {
                "method": "GET",
                "url_pattern": "/{name}",
                "request": DummyGetRequest(secret=SecretStr("yolo"), bar=1, name="jon"),
                "expected": HTTPRequest(
                    method="GET",
                    headers={"secret": "yolo"},
                    path={"name": "jon"},
                    body="",
                    querystring={"bar": 1},
                    url_pattern="/{name}",
                ),
            },
            id="post json",
        ),
        pytest.param(
            {
                "method": "POST",
                "url_pattern": "/{name}",
                "request": DummyPostRequest(
                    secret=SecretStr("yolo"), bar=1, name="jon", foo="bar"
                ),
                "expected": HTTPRequest(
                    method="POST",
                    headers={"secret": "yolo"},
                    path={"name": "jon"},
                    body='{"foo": "bar"}',
                    querystring={"bar": 1},
                    url_pattern="/{name}",
                ),
            },
            id="post json",
        ),
        pytest.param(
            {
                "method": "GET",
                "url_pattern": "/",
                "request": DummyAliasRequestTypes(**{"for": "alice"}),
                "expected": HTTPRequest(
                    method="GET",
                    headers={},
                    path={},
                    body="",
                    querystring={"for": "alice"},
                    url_pattern="/",
                ),
            },
            id="querystring with alias",
        ),
        pytest.param(
            {
                "method": "POST",
                "url_pattern": "/",
                "request": DummyAttachement(
                    foo="foo", bar=Attachment(filename="bar.csv", content=b"csv;bar")
                ),
                "expected": HTTPRequest(
                    method="POST",
                    headers={},
                    path={},
                    body={"foo": "foo"},
                    querystring={},
                    attachments={"bar": ("bar.csv", b"csv;bar", None, {})},
                    url_pattern="/",
                ),
            },
            id="querystring with attachment",
        ),
        pytest.param(
            {
                "method": "POST",
                "url_pattern": "/",
                "request": DummyComplexAttachement(
                    foo=DummyComplex(name="foobar"),
                    bar=Attachment(filename="bar.csv", content=b"csv;bar"),
                ),
                "expected": HTTPRequest(
                    method="POST",
                    headers={},
                    path={},
                    body={
                        "foo": '{"name": "foobar"}',
                    },
                    querystring={},
                    attachments={"bar": ("bar.csv", b"csv;bar", None, {})},
                    url_pattern="/",
                ),
            },
            id="querystring with complex attachment",
        ),
    ],
)
def test_serializer_request(params: Mapping[str, Any]):
    req = serialize_request(params["method"], params["url_pattern"], params["request"])
    assert req == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "srlz": JsonRequestSerializer(),
            "accept": "application/json",
            "expected": True,
        },
        {
            "srlz": JsonRequestSerializer(),
            "accept": "application/json; charset=utf-8",
            "expected": True,
        },
        {
            "srlz": JsonRequestSerializer(),
            "accept": "text/xml",
            "expected": False,
        },
        {
            "srlz": UrlencodedRequestSerializer(),
            "accept": "application/x-www-form-urlencoded",
            "expected": True,
        },
        {
            "srlz": UrlencodedRequestSerializer(),
            "accept": "text/xml",
            "expected": False,
        },
    ],
)
def test_request_serializer_accept(params: Mapping[str, Any]):
    ret = params["srlz"].accept(params["accept"])
    assert ret == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "srlz": JsonRequestSerializer(),
            "data": {"foo": "bar"},
            "expected": '{"foo": "bar"}',
        },
        {
            "srlz": UrlencodedRequestSerializer(),
            "data": {"foo": "bar"},
            "expected": "foo=bar",
        },
        {
            "srlz": UrlencodedRequestSerializer(),
            "data": {"foo": ["bar", "baz"]},
            "expected": "foo=bar&foo=baz",
        },
    ],
)
def test_request_serializer_serialize(params: Mapping[str, Any]):
    ret = params["srlz"].serialize(params["data"])
    assert ret == params["expected"]


def test_register_serializer():
    srlz = MySerializer()
    register_http_body_serializer(srlz)

    httpreq = serialize_request(
        "POST",
        "/",
        DummyPostRequestXML(foo="bar"),
    )

    assert httpreq.body == "<foo/>"

    httpreq = serialize_request(
        "POST",
        "/",
        DummyPostRequestXML(foo="bar", **{"Content-Type": "application/json"}),
    )

    assert httpreq.body == '{"foo": "bar"}'

    unregister_http_body_serializer(srlz)

    with pytest.raises(UnregisteredContentTypeException) as ctx:
        serialize_request(
            "POST",
            "/",
            DummyPostRequestXML(foo="bar"),
        )
    assert (
        str(ctx.value) == "Unregistered content type 'text/xml' in request <foo='bar' "
        "content_type='text/xml'>"
    )


@pytest.mark.parametrize(
    "params",
    [
        pytest.param(
            {
                "raw_response": DummyHTTPRepsonse(
                    200, {"Content-Type": "application/json"}, '{"foo": "bar"}'
                ),
                "expected": HTTPResponse(
                    200, {"Content-Type": "application/json"}, {"foo": "bar"}
                ),
            },
            id="json",
        ),
        pytest.param(
            {
                "raw_response": DummyHTTPRepsonse(
                    200, {"Content-Type": "application/json"}, '{"foo": "bar"'
                ),
                "expected": HTTPResponse(
                    200,
                    {"Content-Type": "application/json"},
                    {"error": '{"foo": "bar"'},
                ),
            },
            id="bad json",
        ),
        pytest.param(
            {
                "raw_response": DummyHTTPRepsonse(
                    200,
                    {"Content-Type": "application/x-www-form-urlencoded"},
                    "x=42&y=1",
                ),
                "expected": HTTPResponse(
                    200,
                    {"Content-Type": "application/x-www-form-urlencoded"},
                    {"x": ["42"], "y": ["1"]},
                ),
            },
            id="urlencoded",
        ),
        pytest.param(
            {
                "raw_response": DummyHTTPRepsonse(204, {}, ""),
                "expected": HTTPResponse(204, {}, ""),
            },
            id="nocontent",
        ),
    ],
)
def test_serialize_response(params: Mapping[str, Any]):
    resp = serialize_response(params["raw_response"])
    assert resp == params["expected"]
