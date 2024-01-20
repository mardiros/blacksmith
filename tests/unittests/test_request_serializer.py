from typing import Any, Mapping

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
from blacksmith.service.request_serializer import serialize_request


class DummyGetRequest(Request):
    secret: SecretStr = HeaderField()
    bar: int = QueryStringField()
    name: str = PathInfoField()


class DummyPostRequest(DummyGetRequest):
    foo: str = PostBodyField()


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
