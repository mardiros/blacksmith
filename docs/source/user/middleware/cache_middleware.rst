HTTP Cache Middleware
=====================

Sometime, for performance reason, caching avoid lots of compute made in
services. Blacksmith comes with a middleware based on redis and that cache
response using the :term:`Cache-Control` HTTP header.

The caching middleware only cache response that have the ``public`` directive
in the ``Cache-Control`` response and cache it depending on the ``max-age``
and the ``age`` of the response.
It also interpret the ``Vary`` response header to create distinct response
depending on the request headers.


It requires an extra dependency `aioredis` installed using the
following command.

::

   pip install blacksmith[caching]

Or using poetry

::

   poetry add blacksmith -E caching

Usage using the async api
-------------------------

.. literalinclude:: cache_middleware_async.py


Usage using the sync api
------------------------

.. literalinclude:: cache_middleware_sync.py




Combining caching and prometheus
--------------------------------

.. important::

   The order of the middleware is important.

GOOD
~~~~

In the example above, prometheus **will not count** cached request:

::

   cache = aioredis.from_url("redis://redis/0")
   sd = AsyncConsulDiscovery()
   metrics = PrometheusMetrics()
   cli = (
      AsyncClientFactory(sd)
      .add_middleware(AsyncHTTPCacheMiddleware(cache, metrics=metrics))
      .add_middleware(AsyncPrometheusMetrics(metrics))
   )


BAD
~~~

In the example above, prometheus **will count** cached request:

::

   cache = aioredis.from_url("redis://redis/0")
   sd = AsyncConsulDiscovery()
   cli = (
      AsyncClientFactory(sd)
      .add_middleware(AsyncPrometheusMetrics())
      .add_middleware(AsyncHTTPCacheMiddleware(cache))
   )

.. warning::

   By adding the cache after the prometheus middleware, the metrics
   ``blacksmith_request_latency_seconds`` will mix the API response
   from the cache and from APIs.


Full example of the http_cache
------------------------------

You will find an example using prometheus and the circuit breaker in the examples directory:

   https://github.com/mardiros/blacksmith/tree/master/examples/http_cache


.. figure:: ../../../../examples/http_cache/screenshot.png

   Example with metrics on http://prometheus.localhost/
