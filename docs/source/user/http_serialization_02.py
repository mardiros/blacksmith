from collections.abc import Sequence
from typing import Any, Optional, Union

from blacksmith import AbstractHttpBodySerializer, register_http_body_serializer
from blacksmith.typing import Json


class MySerializer(AbstractHttpBodySerializer):
    def accept(self, content_type: str) -> bool:
        return content_type == "text/xml+dummy"

    def serialize(self, body: Union[dict[str, Any], Sequence[Any]]) -> str:
        return "<foo/>"

    def deserialize(self, body: bytes, encoding: Optional[str]) -> Json:
        return {"foo": "bar"}


register_http_body_serializer(MySerializer())
