import abc
import json
from collections.abc import Callable, Mapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)
from urllib.parse import parse_qs, urlencode

from pydantic import BaseModel, SecretBytes, SecretStr

# assume we can use deprecated stuff until we support both version
from pydantic.deprecated.json import ENCODERS_BY_TYPE as BASE_TYPES  # type: ignore
from pydantic.fields import FieldInfo
from pydantic.networks import AnyUrl
from pydantic_core import Url as PydantiCoreUrl

from blacksmith.domain.exceptions import UnregisteredContentTypeException
from blacksmith.domain.model.http import (
    HTTPRawResponse,
    HTTPRequest,
    HTTPResponse,
    RequestAttachments,
    RequestBody,
)
from blacksmith.domain.model.params import (
    ATTACHMENT,
    BODY,
    HEADER,
    PATH,
    QUERY,
    Attachment,
    Request,
)
from blacksmith.typing import HttpLocation, HTTPMethod, Json, Url

ENCODERS_BY_TYPE: Mapping[type[Any], Callable[[Any], Any]] = {
    AnyUrl: str,
    PydantiCoreUrl: str,
    **BASE_TYPES,
}

if TYPE_CHECKING:
    from pydantic.typing import IntStr
else:
    IntStr = str


simpletypes = str | int | float | bool


class AbstractHttpBodySerializer(abc.ABC):
    """Request body serializer."""

    @abc.abstractmethod
    def accept(self, content_type: str) -> bool:
        """Return true in case it can handle the request."""

    @abc.abstractmethod
    def serialize(self, body: dict[str, Any] | Sequence[Any]) -> RequestBody:
        """
        Serialize a python simple types to a python request body.

        The body received here is the extracted object from the request model.
        """

    @abc.abstractmethod
    def deserialize(self, body: bytes, encoding: str | None) -> Json:
        """
        Deserialize a raw http response body to a python simple types representation.
        """


class JsonRequestSerializer(AbstractHttpBodySerializer):
    """The default serializer that serialize to json"""

    def accept(self, content_type: str) -> bool:
        return content_type.startswith("application/json")

    def serialize(self, body: dict[str, Any] | Sequence[Any]) -> RequestBody:
        return json.dumps(body, cls=JSONEncoder)

    def deserialize(self, body: bytes, encoding: str | None) -> Json:
        return json.loads(body)


class UrlencodedRequestSerializer(AbstractHttpBodySerializer):
    """A serializer for application/x-www-form-urlencoded request."""

    def accept(self, content_type: str) -> bool:
        return content_type == "application/x-www-form-urlencoded"

    def serialize(self, body: dict[str, Any] | Sequence[Any]) -> RequestBody:
        return urlencode(body, doseq=True)

    def deserialize(self, body: bytes, encoding: str | None) -> Json:
        return parse_qs(body.decode(encoding=encoding or "utf-8", errors="replace"))


class JSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        for typ, serializer in ENCODERS_BY_TYPE.items():
            if isinstance(o, typ):
                return serializer(o)
        return super().default(o)


def get_fields(model: BaseModel) -> Mapping[str, FieldInfo]:
    return model.__class__.model_fields


def get_location(field: FieldInfo) -> HttpLocation:
    extra = field.json_schema_extra
    if extra is None or callable(extra) or "location" not in extra:
        raise TypeError(
            "not a PathInfoField | HeaderField | QueryStringField | PostBodyField"
        )
    return extra["location"]  # type: ignore


def get_value(
    v: simpletypes
    | SecretStr
    | SecretBytes
    | dict[str, simpletypes]
    | list[simpletypes],
    dump_complex_to_json: bool,
) -> simpletypes:
    if dump_complex_to_json and isinstance(v, (dict, list)):
        return json.dumps(v)
    if hasattr(v, "get_secret_value"):
        return v.get_secret_value()  # type: ignore
    return v  # type: ignore


def serialize_part(
    req: "Request", part: dict[IntStr, Any], loc: HttpLocation
) -> dict[str, simpletypes]:
    dump_complex_to_json = loc not in (BODY, QUERY)
    return {
        **{
            k: get_value(v, dump_complex_to_json)
            for k, v in req.model_dump(
                include=part,
                by_alias=True,
                exclude_none=True,
                exclude_defaults=False,
            ).items()
            if v is not None
        },
        **{
            k: get_value(v, dump_complex_to_json)
            for k, v in req.model_dump(
                include=part,
                by_alias=True,
                exclude_none=False,
                exclude_unset=True,
                exclude_defaults=False,
            ).items()
        },
    }


_SERIALIZERS: list[AbstractHttpBodySerializer] = [
    JsonRequestSerializer(),
    UrlencodedRequestSerializer(),
]


def register_http_body_serializer(serializer: AbstractHttpBodySerializer) -> None:
    """Register a serializer to serialize some kind of request."""
    _SERIALIZERS.insert(0, serializer)


def unregister_http_body_serializer(
    serializer: AbstractHttpBodySerializer,
) -> None:
    """
    Unregister a serializer previously added.

    Usefull for testing purpose.
    """
    _SERIALIZERS.remove(serializer)


def serialize_request_body(
    req: "Request", body: dict[str, str], content_type: str | None = None
) -> RequestBody:
    """
    Serialize the body of the request.

    Note that the content_type is optional, but if it is set,

    the request will contains
    """
    if not body and not content_type:
        return ""
    content_type = content_type or "application/json"
    for serializer in _SERIALIZERS:
        if serializer.accept(content_type):
            return serializer.serialize(serialize_part(req, body, "body"))
    raise UnregisteredContentTypeException(content_type, req)


def serialize_request_attachment(
    req: "Request",
    attachments: dict[str, Attachment],
    content_type: str | None = None,
) -> RequestAttachments | None:
    if not attachments:
        return None
    return {
        key: (
            getattr(req, key).filename,
            getattr(req, key).content,
            getattr(req, key).content_type,
            getattr(req, key).headers,
        )
        for key in attachments
    }


def serialize_request(
    method: HTTPMethod,
    url_pattern: Url,
    request_model: Request,
) -> HTTPRequest:
    """
    Serialize :class:`blacksmith.Request` subclasses to :class:`blacksmith.HTTPRequest`.

    While processing an http request, the request models are serialize to an
    intermediate object :class:`blacksmith.HTTPRequest`, that will be passed over
    middleware and finally to the transport in order to build the final http request.

    Note that the body of the :class:`blacksmith.HTTPRequest` is a string, here,
    serialized by a registered serializer.
    """
    req = HTTPRequest(method=method, url_pattern=url_pattern)
    fields_by_loc: dict[HttpLocation, dict[IntStr, Any]] = {
        HEADER: {},
        PATH: {},
        QUERY: {},
        BODY: {},
        ATTACHMENT: {},
    }
    for name, field in get_fields(request_model).items():
        loc = get_location(field)
        fields_by_loc[loc].update({name: ...})

    headers = serialize_part(request_model, fields_by_loc[HEADER], HEADER)
    req.headers = {key: str(val) for key, val in headers.items()}
    req.path = serialize_part(request_model, fields_by_loc[PATH], PATH)
    req.querystring = cast(
        dict[str, simpletypes | list[simpletypes]],
        serialize_part(request_model, fields_by_loc[QUERY], QUERY),
    )

    req.attachments = serialize_request_attachment(
        request_model,
        fields_by_loc[ATTACHMENT],
    )
    if req.attachments:
        req.body = serialize_part(request_model, fields_by_loc[BODY], ATTACHMENT)
    else:
        req.body = serialize_request_body(
            request_model,
            fields_by_loc[BODY],
            cast(str | None, headers.get("Content-Type")),
        )

    return req


def serialize_response(resp: HTTPRawResponse) -> HTTPResponse:
    """
    Deserialize an http response to the http intermediate representation that will
    become the pydantic based response.
    Basically it parse json bytes a a python structure. But this function is here
    to supports serializations format depending on the content-type.
    """
    json_: Json = ""
    if resp.status_code != 204:
        content_type = resp.headers.get("Content-Type") or "application/json"
        for serializer in _SERIALIZERS:
            if serializer.accept(content_type):
                try:
                    json_ = serializer.deserialize(resp.content, resp.encoding)
                except Exception:
                    json_ = {"error": resp.text}
                else:
                    # we can assume that a serializer will work ?
                    break

    return HTTPResponse(
        status_code=resp.status_code,
        headers=resp.headers,
        json=json_,
    )
