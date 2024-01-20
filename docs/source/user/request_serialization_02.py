from typing import Any, Dict, Sequence, Union

from blacksmith import AbstractRequestBodySerializer, register_request_body_serializer


class MySerializer(AbstractRequestBodySerializer):
    def accept(self, content_type: str) -> bool:
        return content_type == "text/xml+dummy"

    def serialize(self, body: Union[Dict[str, Any], Sequence[Any]]) -> str:
        return "<foo/>"


register_request_body_serializer(MySerializer())
