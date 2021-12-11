import re
from dataclasses import dataclass, field
from typing import (
    Callable,
    Coroutine,
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from ...typing import Url

simpletypes = Union[str, int, float, bool]


class HTTPTimeout:
    """Request timeout."""

    request: float
    connect: float

    def __init__(self, timeout: float = 30.0, connect: float = 15.0):
        self.request = timeout
        self.connect = connect

    def __eq__(self, other):
        return self.request == other.request and self.connect == other.connect


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


def parse_header_links(value: str) -> List[Dict[str, str]]:
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
    links: List[Dict[str, str]] = []
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


Links = Dict[Optional[str], Dict[str, str]]


@dataclass
class HTTPResponse:
    """
    Internal representation of an http response.
    """

    status_code: int
    """HTTP Status code."""
    headers: Dict[str, str]
    """Header of the response."""
    json: Optional[Any]
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
        return ldict


Middleware = Callable[[HTTPRequest], Coroutine[Any, Any, HTTPResponse]]


class HTTPMiddleware:
    """Inject data in http query on every requests."""

    def __init__(self) -> None:
        pass

    def __call__(self, next: Middleware) -> Middleware:
        
        async def handle(req: HTTPRequest) -> HTTPResponse:
            return await next(req)

        return handle


class HTTPAddHeaderdMiddleware(HTTPMiddleware):
    """Generic middleware that inject header."""

    headers: Dict[str, str] = field(default_factory=dict)

    def __init__(self, headers: Dict[str, str]):
        self.headers = headers

    def __call__(self, next: Middleware) -> Middleware:
        async def handle(req: HTTPRequest) -> HTTPResponse:
            req.headers.update(self.headers)
            return await next(req)

        return handle


class HTTPUnauthenticated(HTTPMiddleware):
    """
    Empty Authentication Mechanism.

    This is the default value for every call.
    """


class HTTPAuthorization(HTTPAddHeaderdMiddleware):
    """
    Authentication Mechanism based on the header `Authorization`.

    :param scheme: the scheme of the mechanism.
    :param value: the value that authenticate the user using the scheme.
    """

    def __init__(self, scheme: str, value: str):
        return super().__init__({"Authorization": f"{scheme} {value}"})
