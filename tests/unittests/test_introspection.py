from collections.abc import Mapping
from typing import Any, Literal, Union

import pytest
from pydantic import BaseModel, ValidationError

from blacksmith.shared_utils.introspection import (
    build_pydantic_union,
    is_instance_with_union,
    is_union,
)


class Foo(BaseModel):
    typ: Literal["foo"]


class Bar(BaseModel):
    typ: Literal["bar"]


@pytest.mark.parametrize(
    "params",
    [
        pytest.param(
            {"type": Foo, "params": {"typ": "foo"}, "expected": Foo(typ="foo")},
            id="simple",
        ),
        pytest.param(
            {
                "type": Foo | Bar,
                "params": {"typ": "foo"},
                "expected": Foo(typ="foo"),
            },
            id="union",
        ),
        pytest.param(
            {
                "type": Foo | Bar,
                "params": {"typ": "bar"},
                "expected": Bar(typ="bar"),
            },
            id="union",
        ),
    ],
)
def test_build_pydantic_uniont(params: Mapping[str, Any]):
    req = build_pydantic_union(params["type"], params["params"])
    assert req == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        pytest.param(
            {"type": Foo, "params": {"typ": "bar"}, "err": "Input should be 'foo'"},
            id="simple",
        ),
        pytest.param(
            {
                "type": Foo | Bar,
                "params": {"typ": "baz"},
                "err": "Input should be 'bar'",
            },
            id="union",
        ),
    ],
)
def test_build_pydantic_uniont_error(params: Mapping[str, Any]):
    with pytest.raises(ValidationError) as ctx:
        build_pydantic_union(params["type"], params["params"])
    assert str(ctx.value.errors()[0]["msg"]) == params["err"]


@pytest.mark.parametrize(
    "params",
    [
        pytest.param({"type": str, "value": "bob", "expected": True}, id="str"),
        pytest.param({"type": str, "value": 0.42, "expected": False}, id="str / float"),
        pytest.param(
            {"type": int | str, "value": "bob", "expected": True},
            id="int | str / str",
        ),
        pytest.param(
            {"type": int | str, "value": 42, "expected": True},
            id="int | str / int",
        ),
        pytest.param(
            {"type": int | str, "value": 0.42, "expected": False},
            id="int | str / float",
        ),
    ],
)
def test_is_instance_with_union(params: Mapping[str, Any]):
    resp = is_instance_with_union(params["value"], params["type"])
    assert resp == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        pytest.param({"type": int, "expected": False}, id="int"),
        pytest.param({"type": str, "expected": False}, id="str"),
        pytest.param({"type": int | str, "expected": True}, id="int | str"),
        pytest.param(
            {
                "type": Union[int, str],  # noqa UP007
                "expected": True,
            },
            id="Union[int, str]",
        ),
    ],
)
def test_is_union(params: Mapping[str, Any]):
    assert is_union(params["type"]) is params["expected"]
