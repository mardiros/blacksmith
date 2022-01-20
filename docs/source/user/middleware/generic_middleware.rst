.. _`Generic Middleware`:

Generic Middleware
==================

:class:`blacksmith.PrometheusMetrics`, :class:`blacksmith.CircuitBreaker`,
:class:`blacksmith.HTTPAddHeadersMiddleware` are 
implementation of the :class:`blacksmith.HTTPMiddleware` that can be used to
create new middlewares.

.. note::

   The middleware pattern is very common on http framework, in blacksmith,
   this is the same concept.
   
   The middleware is injected after the serialization of the request, before
   sending the http query, to intercept request and response.

Example of middleware:
----------------------

.. literalinclude:: generic_middleware_async.py


.. note::

   :class:`blacksmith.AsyncHTTPMiddleware` is a base class for all the async 
   middleware, :class:`AsyncMiddleware` is the signature of the function 
   ``handle`` above.

Example of middleware using the synchronous API:
------------------------------------------------

.. literalinclude:: generic_middleware_sync.py
