Caching Middleware
==================

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

.. literalinclude:: cache_middleware.py


Usage using the sync api
------------------------

.. literalinclude:: cache_middleware_sync.py



Full example of the redis_caching
---------------------------------

You will find an example using prometheus and the circuit breaker in the examples directory:

   https://github.com/mardiros/blacksmith/tree/master/examples/redis_caching
