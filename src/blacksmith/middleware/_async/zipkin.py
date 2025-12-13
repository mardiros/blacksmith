"""Trace with zipkin of jaegger."""

import abc
from typing import Any

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.typing import ClientName, Path

from .base import AsyncHTTPMiddleware, AsyncMiddleware


class AbstractTraceContext(abc.ABC):
    """
    Interface of the trace context for the middleware.

    See examples with starlette-zipking for an implementation.
    """

    @classmethod
    @abc.abstractmethod
    def make_headers(cls) -> dict[str, str]:
        """Build headers for the sub requests."""

    @abc.abstractmethod
    def __init__(self, name: str, kind: str = "SERVER") -> None:
        """Create a trace span for the current context."""

    @abc.abstractmethod
    def tag(self, key: str, value: str) -> "AbstractTraceContext":
        """Tag the span"""

    @abc.abstractmethod
    def annotate(
        self, value: str | None, ts: float | None = None
    ) -> "AbstractTraceContext":
        """Annotate the span"""

    @abc.abstractmethod
    def __enter__(self) -> "AbstractTraceContext":
        """Make the created trace span of the current context the active span."""

    @abc.abstractmethod
    def __exit__(self, *exc: Any) -> None:
        """
        Ends the created trace span of the context, it parents become the active span.
        """


class AsyncZipkinMiddleware(AsyncHTTPMiddleware):
    """
    Zipkin Middleware based on an abstract context manager.

    :param trace: A deferred context manager that manage the trace span stack.
    """

    def __init__(self, trace: type[AbstractTraceContext]) -> None:
        self.trace = trace

    def __call__(self, next: AsyncMiddleware) -> AsyncMiddleware:
        async def handle(
            req: HTTPRequest,
            client_name: ClientName,
            path: Path,
            timeout: HTTPTimeout,
        ) -> HTTPResponse:
            name = f"{req.method} {path.format(**req.path)}"

            with self.trace(name, "CLIENT") as child_span:
                headers = self.trace.make_headers()
                req.headers.update(headers)

                child_span.tag("blacksmith.client_name", client_name)

                child_span.tag("http.path", path)
                if req.querystring:
                    child_span.tag("http.querystring", repr(req.querystring))
                try:
                    resp = await next(req, client_name, path, timeout)
                except HTTPError as exc:
                    child_span.tag("http.status_code", str(exc.response.status_code))
                    child_span.tag("error", "true")
                    raise
                else:
                    child_span.tag("http.status_code", str(resp.status_code))
                    return resp

        return handle
