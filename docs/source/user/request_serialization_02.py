from typing import Any, Dict, Optional, Sequence, Union

from blacksmith import AbstractHttpBodySerializer, register_http_body_serializer
from blacksmith.typing import Json


class MySerializer(AbstractHttpBodySerializer):
    def accept(self, content_type: str) -> bool:
        return content_type == "text/xml+dummy"

    def serialize(self, body: Union[Dict[str, Any], Sequence[Any]]) -> str:
        return "<foo/>"

    def deserialize(self, body: bytes, encoding: Optional[str]) -> Json:
        return {"foo": "bar"}


register_http_body_serializer(MySerializer())
