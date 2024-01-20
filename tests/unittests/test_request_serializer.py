import json
from datetime import datetime
from typing import Any, Mapping, Optional

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
from blacksmith.service.request_serializer import (
    QUERY,
    JSONEncoder,
    get_location,
    serialize_part,
    serialize_request,
)


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
