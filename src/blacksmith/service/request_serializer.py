import json
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Union, cast

from pydantic import BaseModel, SecretBytes, SecretStr
from pydantic.fields import FieldInfo

from blacksmith.domain.model.http import HTTPRequest
from blacksmith.domain.model.params import Request
from blacksmith.typing import HttpLocation, HTTPMethod, Url

# assume we can use deprecated stuff until we support both version
try:
    # pydantic 2
    from pydantic.deprecated.json import ENCODERS_BY_TYPE  # type: ignore
except ImportError:  # type: ignore # coverage: ignore
    # pydantic 1
    from pydantic.json import ENCODERS_BY_TYPE  # type: ignore  # coverage: ignore

if TYPE_CHECKING:
    from pydantic.typing import IntStr
else:
    IntStr = str


PATH: HttpLocation = "path"
HEADER: HttpLocation = "headers"
QUERY: HttpLocation = "querystring"
BODY: HttpLocation = "body"
simpletypes = Union[str, int, float, bool]


class JSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        for typ, serializer in ENCODERS_BY_TYPE.items():
            if isinstance(o, typ):
                return serializer(o)
        return super(JSONEncoder, self).default(o)


def get_fields(model: BaseModel) -> Mapping[str, FieldInfo]:
    if hasattr(model, "model_fields"):
        return model.model_fields
    return model.__fields__  # pydantic 1


def get_location(field: Any) -> HttpLocation:
    # field is of type FieldInfo, which differ on pydantic 2 and pydantic 1
    if hasattr(field, "json_schema_extra"):
        extra = field.json_schema_extra
    elif hasattr(field, "field_info"):
        extra = field.field_info.extra
    else:
        raise ValueError(f"{field} is not a FieldInfo")
    return extra["location"]


def get_value(v: Union[simpletypes, SecretStr, SecretBytes]) -> simpletypes:
    if hasattr(v, "get_secret_value"):
        return getattr(v, "get_secret_value")()
    return v  # type: ignore


def serialize_part(req: "Request", part: Dict[IntStr, Any]) -> Dict[str, simpletypes]:
    return {
        **{
            k: get_value(v)
            for k, v in req.dict(
                include=part,
                by_alias=True,
                exclude_none=True,
                exclude_defaults=False,
            ).items()
            if v is not None
        },
        **{
            k: get_value(v)
            for k, v in req.dict(
                include=part,
                by_alias=True,
                exclude_none=False,
                exclude_unset=True,
                exclude_defaults=False,
            ).items()
        },
    }


def serialize_body(
    req: "Request", body: Dict[str, str], content_type: Optional[str] = None
) -> str:
    """Serialize the body of the request. In case there is some."""
    if not body and not content_type:
        return ""
    if content_type is None or content_type.startswith("application/json"):
        return json.dumps(serialize_part(req, body), cls=JSONEncoder)
    return ""


def serialize_request(
    method: HTTPMethod,
    url_pattern: Url,
    request_model: Request,
) -> HTTPRequest:
    req = HTTPRequest(method=method, url_pattern=url_pattern)
    fields_by_loc: Dict[HttpLocation, Dict[IntStr, Any]] = {
        HEADER: {},
        PATH: {},
        QUERY: {},
        BODY: {},
    }
    for name, field in get_fields(request_model).items():
        loc = get_location(field)
        fields_by_loc[loc].update({name: ...})

    headers = serialize_part(request_model, fields_by_loc[HEADER])
    req.headers = {key: str(val) for key, val in headers.items()}
    req.path = serialize_part(request_model, fields_by_loc[PATH])
    req.querystring = cast(
        Dict[str, Union[simpletypes, List[simpletypes]]],
        serialize_part(request_model, fields_by_loc[QUERY]),
    )

    req.body = serialize_body(
        request_model,
        fields_by_loc[BODY],
        cast(Optional[str], headers.get("Content-Type")),
    )
    return req
