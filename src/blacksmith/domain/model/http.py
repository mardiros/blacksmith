import re
from collections.abc import AsyncIterable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import (
    Any,
    Optional,
    Protocol,
    Union,
    cast,
)

from blacksmith.typing import HTTPMethod, Json, Url

simpletypes = Union[str, int, float, bool]
Links = dict[Optional[str], dict[str, str]]
RequestBody = Union[
    str,
    bytes,
    Iterable[bytes],
    AsyncIterable[bytes],
    # a mapping is passed if there is attachment.
    Mapping[str, simpletypes],
]
RequestAttachments = dict[
    str,
    tuple[str, bytes, Optional[str], Mapping[str, str]],
]


class HTTPTimeout:
    """Request timeout."""

    read: float
    connect: float

    def __init__(self, read: float = 30.0, connect: float = 15.0) -> None:
        self.read = read
        self.connect = connect

    def __eq__(self, other: Any) -> bool:
        return self.read == other.read and self.connect == other.connect


@dataclass
class HTTPRequest:
    """
    Internal representation of an http request.

    Note that the HTTP method is not present, because the method is
    the funcion called.

    The HTTP Request is filled out using the
    :class:`blacksmith.domain.model.params.Request` schema.
    """

    method: HTTPMethod
    url_pattern: Url
    # the property match with the "location" of feaut
    path: dict[str, simpletypes] = field(default_factory=dict)
    querystring: dict[str, Union[simpletypes, list[simpletypes]]] = field(
        default_factory=dict
    )
    headers: dict[str, str] = field(default_factory=dict)
    body: RequestBody = ""
    attachments: Optional[RequestAttachments] = field(default=None)

    @property
    def url(self) -> str:
        return self.url_pattern.format(**self.path)


def parse_header_links(value: str) -> list[dict[str, str]]:
    """
    Returns a list of parsed link headers, for more info see:
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Link

    The generic syntax of those is:

    ::

        Link: < uri-reference >; param1=value1; param2="value2"

    So for instance:

    Link; '<http:/.../front.jpeg>; type="image/jpeg",<http://.../back.jpeg>;'
    would return

    ::

        [
            {"url": "http:/.../front.jpeg", "type": "image/jpeg"},
            {"url": "http://.../back.jpeg"},
        ]

    .. note::

        Stolen code from httpx _utils.py (private method)


    :param value: HTTP Link entity-header field
    :return: list of parsed link headers
    """
    links: list[dict[str, str]] = []
    replace_chars = " '\""
    value = value.strip(replace_chars)
    if not value:
        return links
    for val in re.split(", *<", value):
        try:
            url, params = val.split(";", 1)
        except ValueError:
            url, params = val, ""
        link = {"url": url.strip("<> '\"")}
        for param in params.split(";"):
            try:
                key, value = param.split("=")
            except ValueError:
                break
            link[key.strip(replace_chars)] = value.strip(replace_chars)
        links.append(link)
    return links


class HTTPRawResponse(Protocol):
    """
    Internal representation of an http response.
    This format is used to deserialize the response body to the HTTPResponse.
    """

    status_code: int
    headers: Mapping[str, str]
    """
    The headers response implmentation should be key insensitive, http standard.

    Blacksmith rely on httpx as the default implementation, key are insensitive.
    """

    @property
    def content(self) -> bytes: ...

    @property
    def text(self) -> str: ...

    @property
    def encoding(self) -> str: ...


@dataclass
class HTTPResponse:
    """
    Intermediate representation of an http response.

    In this representation, the response body has been parsed to the property ``json``,
    which is a python structure containing simple python types. This http response
    representation will be used create pydantic response object.
    """

    status_code: int
    """HTTP Status code."""
    headers: Mapping[str, str]
    """Header of the response."""
    json: Json
    """Json Body of the response."""

    @property
    def links(self) -> Links:
        header = self.headers.get("link")
        ldict = {}
        if header:
            links = parse_header_links(header)
            for link in links:
                key = link.get("rel") or link.get("url")
                ldict[key] = link
        return cast(Links, ldict)
