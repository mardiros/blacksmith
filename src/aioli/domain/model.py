from dataclasses import dataclass, field
from functools import partial
from typing import Generator, TYPE_CHECKING, Any, Dict, List, Optional, Union, cast
from attr.setters import frozen

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pydantic.typing import IntStr
else:
    IntStr = str

from ..typing import HttpLocation, Url

PATH: HttpLocation = "path"
HEADER: HttpLocation = "headers"
QUERY: HttpLocation = "querystring"
BODY: HttpLocation = "body"


PathInfoField = partial(Field, location=PATH)
"""Declare field that are serialized to the path info."""
HeaderField = partial(Field, location=HEADER)
"""Declare field that are serialized in http request header."""
QueryStringField = partial(Field, location=QUERY)
"""Declare field that are serialized in the http querystring."""
PostBodyField = partial(Field, location=BODY)
"""Declare field that are serialized in the json document."""

simpletypes = Union[str, int, float, bool]


@dataclass(frozen=True)
class HTTPAuthentication:
    """Authentication Mechanism."""

    headers: Dict[str, str] = field(default_factory=dict)


class HTTPUnauthenticated(HTTPAuthentication):
    """
    Empty Authentication Mechanism.

    This is the default value for every call.
    """

    def __init__(self):
        return super().__init__(headers={})


class AuthorizationHttpAuthentication(HTTPAuthentication):
    """
    Authentication Mechanism based on the header `Authorization`.

    :param scheme: the scheme of the mechanism.
    :param value: the value that authenticate the user using the scheme.
    """

    def __init__(self, scheme: str, value: str):
        return super().__init__(headers={"Authorization": f"{scheme} {value}"})


@dataclass
class HTTPRequest:
    """
    Internal representation of an http request.

    Note that the HTTP method is not present, because the method is
    the funcion called.

    The HTTP Request is filled out using the :class:`.Request` schema.
    """

    url_pattern: Url
    # the property match with the "location" of feaut
    path: Dict[str, simpletypes] = field(default_factory=dict)
    querystring: Dict[str, simpletypes] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: str = ""

    @property
    def url(self):
        return self.url_pattern.format(**self.path)

    def merge_authentication(self, authent: HTTPAuthentication) -> "HTTPRequest":
        """Get the http request with the authentication information."""
        headers = self.headers.copy()
        headers.update(authent.headers)
        return HTTPRequest(
            url_pattern=self.url_pattern,
            path=self.path.copy(),
            querystring=self.querystring.copy(),
            headers=headers,
            body=self.body,
        )


@dataclass
class HTTPResponse:
    """
    Internal representation of an http response.
    """

    status_code: int
    """HTTP Status code."""
    json: Optional[Any]
    """Json Body of the response."""


class Request(BaseModel):
    """
    Request Params Model.

    Fields must use subclass :func:`.PathInfoField`, :func:`.HeaderField`,
    :func:`.QueryStringField` or :func:`.PostBodyField` to declare each fields.
    """

    def to_http_request(self, url_pattern: Url) -> HTTPRequest:
        """Convert the request params to an http request in order to serialize
        the http request for the client.
        """
        req = HTTPRequest(url_pattern)
        fields_by_loc: Dict[HttpLocation, Dict[IntStr, Any]] = {
            HEADER: {},
            PATH: {},
            QUERY: {},
            BODY: {},
        }
        for key, field in self.__fields__.items():
            loc = cast(HttpLocation, field.field_info.extra["location"])
            fields_by_loc[loc].update({field.name: ...})

        headers = self.dict(
            include=fields_by_loc[HEADER], by_alias=True, exclude_none=True
        )
        req.headers = {key: str(val) for key, val in headers.items()}
        req.path = self.dict(
            include=fields_by_loc[PATH], by_alias=True, exclude_none=False
        )
        req.querystring = self.dict(
            include=fields_by_loc[QUERY], by_alias=True, exclude_none=True
        )
        req.body = self.json(
            include=fields_by_loc[BODY], by_alias=True, exclude_none=False
        )
        return req


class Response(BaseModel):
    """Response Model."""

    @classmethod
    def from_http_response(cls, response: HTTPResponse) -> Optional["Response"]:
        """Build the response from the given HTTPResponse."""
        if response.json:
            return cls(**response.json)

    @classmethod
    def from_http_collection(
        cls, response: HTTPResponse
    ) -> Generator["Response", None, None]:
        """Yield responses from the given HTTPResponse."""
        if response.json:
            for item in response.json:
                yield cls(**item)
