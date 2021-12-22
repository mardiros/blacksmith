"""Collect metrics based on prometheus."""

import abc
from typing import TYPE_CHECKING, Any, Callable, Dict, Type

from aiozipkin import span

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse
from blacksmith.typing import ClientName, HttpMethod, Path

from .base import HTTPMiddleware, Middleware


class AbtractTraceContext(abc.ABC):
    @abc.abstractclassmethod
    def make_headers(cls) -> Dict[str, str]:
        """Build headers for the sub requests."""

    @abc.abstractmethod
    def __call__(self, name: str, type: str) -> "AbtractTraceContext":
        pass

    @abc.abstractmethod
    def tag(self, tab_name: str, tag_val: str) -> None:
        pass

    @abc.abstractmethod
    def __enter__(self) -> "AbtractTraceContext":
        pass

    @abc.abstractmethod
    def __exit__(self, *exc: Any):
        pass


class ZipkinMiddleware(HTTPMiddleware):
    """
    Zipkin Middleware based on aiozipkin
    """

    def __init__(self, trace: AbtractTraceContext) -> None:
        self.trace = trace

    def __call__(self, next: Middleware) -> Middleware:
        async def handle(
            req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
        ) -> HTTPResponse:

            try:
                name = f"{method} {path.format(**req.path)}"
            except KeyError:
                name = f"{method} {path}"

            with self.trace(name, "CLIENT") as child_span:
                headers = self.trace.make_headers()
                req.headers.update(headers)

                child_span.tag("blacksmith.client_name", client_name)

                child_span.tag("http.path", path)
                if req.querystring:
                    child_span.tag("http.querystring", repr(req.querystring))
                resp = await next(req, method, client_name, path)
                child_span.tag("http.status_code", str(resp.status_code))
                if resp.status_code >= 400:
                    child_span.tag("error", "true")
                return resp

        return handle
