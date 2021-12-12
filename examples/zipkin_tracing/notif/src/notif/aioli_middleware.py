from typing import cast

from notif.zk_middleware import Trace
from starlette.types import ASGIApp, Receive, Scope, Send

from blacksmith import ClientFactory, ConsulDiscovery
from blacksmith.domain.model import HTTPAddHeadersMiddleware


class BlacksmithMiddleware:
    """
    Middleware to inject a aoili client factory in the asgi scope.


    The client is fowarding zipkin header to track api calls.
    """

    def __init__(
        self,
        app: ASGIApp,
    ):
        self.app = app
        self.sd = ConsulDiscovery()
        self.cli = ClientFactory(self.sd)
        self.middleware = HTTPAddHeadersMiddleware(headers={})
        self.cli.add_middleware(self.middleware)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http"]:
            await self.app(scope, receive, send)
            return

        trace = cast(Trace, scope.get("trace"))
        if trace is not None:
            self.middleware.headers = trace.http_headers
        scope["blacksmith_client"] = self.cli
        await self.app(scope, receive, send)
