Middleware
==========

Blacksmith is extensible by adding middleware between the resource contracts
and the real http query.

Users can create their own middleware but blacksmith comes with its lists
of usefull middlewares listed here.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   authorization
   prometheus_middleware
   zipkin_middleware
   caching_middleware
   http_middleware
   circuit_breaker_middleware
   generic_middleware
