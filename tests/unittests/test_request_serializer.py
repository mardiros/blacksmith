import json
from datetime import datetime
from typing import Any, Dict, Mapping, Optional, Sequence, Union

import pytest
from pydantic import SecretStr

from blacksmith import (
    HeaderField,
    HTTPRequest,
    PathInfoField,
    PostBodyField,
    QueryStringField,
    Request,
)
from blacksmith.domain.exceptions import UnregisteredContentTypeException
from blacksmith.service.request_serializer import (
    QUERY,
    AbstractRequestBodySerializer,
    JSONEncoder,
    JsonRequestSerializer,
    UrlencodedRequestSerializer,
    get_location,
    register_request_body_serializer,
    serialize_body,
    serialize_part,
    serialize_request,
    unregister_request_body_serializer,
)


class GetRequest(Request):
    ...


class DummyGetRequest(Request):
    secret: SecretStr = HeaderField()
    bar: int = QueryStringField()
    name: str = PathInfoField()


class DummyPostRequest(DummyGetRequest):
    foo: str = PostBodyField()


def test_json_encoder() -> None:
    assert (
        json.dumps({"date": datetime(2020, 10, 5)}, cls=JSONEncoder)
        == '{"date": "2020-10-05T00:00:00"}'
    )

    with pytest.raises(TypeError) as ctx:
        json.dumps({"oops": object()}, cls=JSONEncoder)
    assert str(ctx.value) == "Object of type object is not JSON serializable"


def test_get_location_from_pydantic_v2() -> None:
    class DummyFieldInfo:
        json_schema_extra = {"location": QUERY}

    assert get_location(DummyFieldInfo()) == QUERY


def test_get_location_from_pydantic_v1() -> None:
    class DummyFieldInfo:
        class field_info:
            extra = {"location": QUERY}

    assert get_location(DummyFieldInfo()) == QUERY


def test_get_location_raises_value_error() -> None:
    class Dummy:
        def __str__(self):
            return "dummy"

    with pytest.raises(ValueError) as ctx:
        get_location(Dummy())
    assert str(ctx.value) == "dummy is not a FieldInfo"


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
    )
    assert obj == {
        "name": "Jane",
        "age": 10,
        "city": "Saint Palais s/mer",
        "state": None,
        "country": "FR",
    }


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
def test_serialize_body(params: Mapping[str, Any]):
    body = serialize_body(params["req"], params["body"], params["content_type"])
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
    class MySerializer(AbstractRequestBodySerializer):
        def accept(self, content_type: str) -> bool:
            return content_type == "text/xml"

        def serialize(self, body: Union[Dict[str, Any], Sequence[Any]]) -> str:
            return "<foo/>"

    srlz = MySerializer()
    register_request_body_serializer(srlz)

    class DummyPostRequestXML(Request):
        foo: str = PostBodyField()
        content_type: str = HeaderField(default="text/xml", alias="Content-Type")

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

    unregister_request_body_serializer(srlz)

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
