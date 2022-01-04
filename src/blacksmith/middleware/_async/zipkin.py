"""Trace with zipkin of jaegger."""

import abc
from typing import Any, Dict, Optional

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse
from blacksmith.typing import ClientName, HttpMethod, Path

from .base import HTTPMiddleware, Middleware


class AbtractTraceContext(abc.ABC):
    """
    Interface of the trace context for the middleware.

    See examples with starlette-zipking for an implementation.
    """

    @abc.abstractclassmethod
    def make_headers(cls) -> Dict[str, str]:
        """Build headers for the sub requests."""

    @abc.abstractmethod
    def __init__(self, name: str, kind: str = "SERVER") -> None:
        """Create a trace span for the current context."""

    @abc.abstractmethod
    def tag(self, key: str, value: str) -> "AbtractTraceContext":
        """Tag the span"""

    @abc.abstractmethod
    def annotate(
        self, value: Optional[str], ts: Optional[float] = None
    ) -> "AbtractTraceContext":
        """Annotate the span"""

    @abc.abstractmethod
    def __enter__(self) -> "AbtractTraceContext":
        """Make the created trace span of the current context the active span."""

    @abc.abstractmethod
    def __exit__(self, *exc: Any):
        """
        Ends the created trace span of the context, it parents become the active span.
        """


class ZipkinMiddleware(HTTPMiddleware):
    """
    Zipkin Middleware based on an abstract context manager.

    :param trace: A deferred context manager that manage the trace span stack.
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
