"""Collect metrics based on prometheus."""

from typing import TYPE_CHECKING, Any, Callable

from aiozipkin import span

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse
from blacksmith.typing import ClientName, HttpMethod, Path

from .base import HTTPMiddleware, Middleware


if TYPE_CHECKING:
    try:
        from aiozipkin import SpanAbc, Tracer
    except ImportError:
        pass
    GetRootSpan = Callable[[], "SpanAbc"]
    GetTracer = Callable[[], "Tracer"]
else:
    GetRootSpan = Callable[[], Any]
    GetTracer = Callable[[], Any]


class ZipkinMiddleware(HTTPMiddleware):
    """
    Zipkin Middleware based on aiozipkin
    """

    def __init__(self, get_root_span: GetRootSpan, get_tracer: GetTracer) -> None:
        self.get_root_span = get_root_span
        self.get_tracer = get_tracer

    def __call__(self, next: Middleware) -> Middleware:
        async def handle(
            req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
        ) -> HTTPResponse:
            root_span = self.get_root_span()
            tracer = self.get_tracer()
            with tracer.new_child(root_span.context) as child_span:
                headers = child_span.context.make_headers()
                child_span.kind("CLIENT")
                req.headers.update(headers)
                try:
                    child_span.name(f"{method} {path.format(**req.path)}")
                except KeyError:
                    child_span.name(f"{method} {path}")

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
