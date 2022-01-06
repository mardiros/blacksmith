.. _`Generic Middleware`:

Generic Middleware
==================

`PrometheusMetrics`, `CircuitBreaker`, `HTTPAddHeadersMiddleware` are 
implementation of the `HTTPMiddleware` that can be used to create own
middleware.

The middleware pattern is very common on http framework, in blacksmith, this
is the same concept, the middleware is injected after the serialization
of the request, before sending the http query, to intercept request
and response.

Example of middleware:
----------------------

.. literalinclude:: generic_middleware.py


.. note::

   :class:`blacksmith.AsyncHTTPMiddleware` is a base class for all the async 
   middleware, :class:`AsyncMiddleware` is the signature of the function 
   ``handle`` above.

Example of middleware using the synchronous API:
------------------------------------------------

.. literalinclude:: generic_middleware_sync.py
