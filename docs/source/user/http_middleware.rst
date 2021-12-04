HTTP Middlewares
================

Aioli let permit to inject headers on every requests.

Here is a dummy example.

::

   class DummyMiddleware(HTTPMiddleware):
      def __init__(self):
         super().__init__(headers={"x-request-header": "foo"})

   dummy_middleware = DummyMiddleware()

   sd = StaticDiscovery({("api", None): "http://srv:8000/"})
   cli = ClientFactory(sd)
   cli.add_middleware(dummy_middleware)


Create a middleware to trace metrics using zipkin
-------------------------------------------------

The middleware is usefull to forward parameter in an http context.

For example, using zipkin, some headers has to be passed to sub services,
to achieve this, lets create a simple middleware that forward the headers.


::

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

         # The trace is managed by another middleware.
         trace = cast(Trace, scope.get("trace"))
         if trace is not None:
               self.middleware.headers=trace.http_headers
         scope["aioli_client"] = self.cli
         await self.app(scope, receive, send)
