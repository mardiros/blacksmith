from dataclasses import dataclass, field
from functools import partial
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field
from ..typing import HttpLocation, Url

PATH: HttpLocation = "PATH"
HEADER: HttpLocation = "HEADER"
QUERY: HttpLocation = "QUERY"
BODY: HttpLocation = "BODY"


PathInfoField = partial(Field, location=PATH)
"""Declare field that are serialized to the path info."""
HeaderField = partial(Field, location=HEADER)
"""Declare field that are serialized in http request header."""
QueryStringField = partial(Field, location=QUERY)
"""Declare field that are serialized in the http querystring."""
PostBodyField = partial(Field, location=BODY)
"""Declare field that are serialized in the json document."""

simpletypes = Union[str, int, float, bool]


@dataclass
class HTTPRequest:
    url_pattern: Url
    path: Dict[str, simpletypes] = field(default_factory=dict)
    querystring: Dict[str, simpletypes] = field(default_factory=dict)
    header: Dict[str, str] = field(default_factory=dict)
    body: Dict[str, Any] = field(default_factory=dict)

    @property
    def url(self):
        return self.url_pattern.format(**self.path)


@dataclass
class HTTPResponse:
    status_code: int
    json: Optional[Any]


class Params(BaseModel):
    """
    HTTP Request Params Model.

    Fields must use subclass PathInfoField, HeaderField, QueryStringField or
    PostBodyField to declare each fields.
    """

    def to_http_request(self, url_pattern: Url) -> HTTPRequest:
        """Convert the Params to an http request in order to serialize
        the http request for the client.
        """
        req = HTTPRequest(url_pattern)
        for key, field in self.__fields__.items():
            loc = field.field_info.extra["location"].lower()
            val = getattr(self, key)
            if loc == "header":
                val = str(val)
            getattr(req, loc)[field.name] = val
        return req


class Response(BaseModel):
    """HTTP Response Model."""

    @classmethod
    def from_http_response(cls, response: HTTPResponse) -> Optional["Response"]:
        if response.json:
            return cls(**response.json)
