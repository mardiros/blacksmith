HTTP Middlewares
================

Blacksmith let permit to inject headers on every requests.

Here is a simple example where a header is injected, and may be updated
during its lifetime.

::

   from blacksmith import HTTPAddHeadersMiddleware
   dummy_middleware = HTTPAddHeadersMiddleware({"x-request-header": "foo"})

   sd = StaticDiscovery({("api", None): "http://srv:8000/"})
   cli = ClientFactory(sd)
   cli.add_middleware(dummy_middleware)

   dummy_middleware.headers["x-request-header"] = "bar"
