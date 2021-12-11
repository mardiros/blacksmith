import socket
from types import TracebackType
from typing import Optional, Type, cast

import aiozipkin as az
from aiozipkin.helpers import make_context, make_headers
from aiozipkin.mypy_types import Headers
from aiozipkin.span import SpanAbc
from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

try:
    from aioli import ConsulDiscovery
except ImportError:

    class ConsulDiscovery:
        async def get_endpoint(self, service, version):
            raise RuntimeError("aioli package is not installed")


class Trace:
    """Represent a root trace for every new http request."""

    def __init__(self, request: Request, span: SpanAbc):
        self._request = request
        self._span = span

    @property
    def http_headers(self) -> Headers:
        """Get HTTP Headers to inject in the http response."""
        return make_headers(self._span.context)

    def new_child(self, span_name: str) -> "Trace":
        """Create a child span for the current trace."""
        # There is no nested trace in our case/implem, because
        # we don't need it.
        span = self._span.new_child(span_name)
        span.kind(az.CLIENT)
        return Trace(self._request, span)

    async def __aenter__(self):
        self._span.__enter__()
        self._parent_trace = self._request.scope.get("trace")
        self._request.scope["trace"] = self
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[Exception]],
        exc: Optional[Exception],
        tb: Optional[TracebackType],
    ) -> Optional[bool]:
        self._span.annotate("end processing view")
        self._span.__exit__(exc_type, exc, tb)
        self._request.scope["trace"] = self._parent_trace


class Tracer:
    """Trace Factory."""

    def __init__(
        self,
        zipkin_endpoint: str,
        service_name: str,
        ipv4: str,
        ipv6: Optional[str],
        port: Optional[int],
        sample_rate: float,
    ):
        self.service_endpoint = az.create_endpoint(
            service_name, ipv4=ipv4, ipv6=ipv6, port=port
        )

        self.zipkin_endpoint = zipkin_endpoint
        self.sample_rate = sample_rate
        self._tracer = None

    async def __call__(self, request: Request) -> Trace:
        """Create the root trace on incoming http query."""
        if self._tracer is None:
            self._tracer = await az.create(
                self.zipkin_endpoint,
                self.service_endpoint,
                sample_rate=self.sample_rate,
            )

        context = make_context(request.headers)
        if context is None:
            root_trace = self._tracer.new_trace(True)
        else:
            root_trace = self._tracer.new_child(context)

        path = cast(str, request.scope.get("root_path", "")) + cast(
            str, request.scope.get("path")
        )
        method = request.method
        path = cast(str, request.scope.get("root_path", "")) + cast(
            str, request.scope.get("path")
        )
        path_params = request.path_params

        root_trace.name(f"{method} {path}")
        root_trace.tag("span_type", "root")
        root_trace.tag("http.path", path)
        if path_params:
            root_trace.tag("http.params", str(repr(path_params)))
        root_trace.kind(az.CLIENT)
        return Trace(request, root_trace)


class ZipkinMiddleware:
    """
    Middleware for tracing with zipkin.
    """

    def __init__(
        self,
        app: ASGIApp,
        service_name: str,
        sample_rate: float = 1.0,
        endpoint: str = "",
    ):
        self.app = app
        self.service_name = service_name
        self.ipv4 = socket.gethostbyname(socket.gethostname())
        self._endpoint = endpoint.rstrip("/")
        self._tracer = None
        self.sample_rate = sample_rate

    async def get_tracer(self):
        if self._tracer is None:
            if not self._endpoint:
                sd = ConsulDiscovery()
                self._endpoint = await sd.get_endpoint("zipkin", None)
            srv = f"{self._endpoint}/api/v2/spans"
            self._tracer = Tracer(
                srv,
                self.service_name,
                socket.gethostbyname(socket.gethostname()),
                None,
                None,
                self.sample_rate,
            )
        return self._tracer

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http"]:
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        tracer = await self.get_tracer()
        # create and setup new trace
        # we call the private method to get the root context.
        root_trace = await tracer(request)
        async with root_trace:

            async def send_with_headers(message: Message):
                if message["type"] == "http.response.start":
                    headers = MutableHeaders(raw=message["headers"])
                    for key, val in root_trace.http_headers.items():
                        headers[key] = val
                await send(message)

            await self.app(scope, receive, send_with_headers)
