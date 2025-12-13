from collections.abc import Mapping
from typing import (
    Any,
    Union,
    get_origin,
)

from pydantic import ValidationError

try:
    from types import UnionType  # type: ignore
except ImportError:  # coverage: ignore
    # python 3.9 compat
    UnionType = Union  # type: ignore


def is_union(typ: type[Any]) -> bool:
    type_origin = get_origin(typ)
    if type_origin:
        if type_origin is Union:  # Union[T, U] or even Optional[T]
            return True

        if type_origin is UnionType:  # T | U
            return True
    return False


def is_instance_with_union(val: Any, typ: type[Any]) -> bool:
    # isinstance does not support union type in old interpreter,
    if is_union(typ):
        r = [isinstance(val, t) for t in typ.__args__]  # type: ignore
        return any(r)
    return isinstance(val, typ)


def build_pydantic_union(typ: Any, params: Mapping[str, Any]) -> Any:
    if is_union(typ):
        err: Exception | None = None
        for t in typ.__args__:  # type: ignore
            try:
                return build_pydantic_union(t, params)  # type: ignore
            except ValidationError as e:
                err = e
        if err:
            raise err
    return typ.model_validate(params)
