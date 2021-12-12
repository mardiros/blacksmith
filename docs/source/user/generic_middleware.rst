Generic Middleware
==================

`PrometheusMetrics`, `CircuitBreaker`, `HTTPAddHeadersMiddleware` are 
implementation of the `HTTPMiddleware` that can be used to create own
middleware.

The middleware pattern is very common on http framework, in aioli, this
is the same concept, the middleware is injected after the serialization
of the request, before sending the http query, to intercept request
and response.

Example of middleware:

::

   from aioli import HTTPMiddleware, Middleware

   class HTTPPrintMiddleware(HTTPMiddleware):
      """Inject data in http query on every requests."""

      def __call__(self, next: Middleware) -> Middleware:
         async def handle(
               req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
         ) -> HTTPResponse:
               print(f">>> {req}")
               resp = await next(req, method, client_name, path)
               print(f"<<< {resp}")
               return resp

         return handle


`HTTPMiddleware` is a base class for all the middleware, Middleware is the
signature of the function `handle` above.
