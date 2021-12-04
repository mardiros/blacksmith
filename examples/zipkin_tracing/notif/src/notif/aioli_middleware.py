from typing import cast

from starlette.types import ASGIApp,Receive, Scope, Send

from aioli import ClientFactory, ConsulDiscovery
from aioli.domain.model import HTTPMiddleware

from notif.zk_middleware import Trace


class AioliMiddleware:
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
        self.middleware = HTTPMiddleware(headers={})
        self.cli.add_middleware(self.middleware)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http"]:
            await self.app(scope, receive, send)
            return

        trace = cast(Trace, scope.get("trace"))
        if trace is not None:
            self.middleware.headers=trace.http_headers
        scope["aioli_client"] = self.cli
        await self.app(scope, receive, send)
