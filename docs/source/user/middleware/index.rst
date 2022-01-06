Middleware
==========

Blacksmith is extensible by adding middleware between the resource 
contracts and the real http query.

For example, requests may share a security secret that make not parts
of the contract of a route.

.. note::

   Users can create their own middleware but blacksmith comes with its lists
   of usefull middlewares listed here.


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   authorization
   circuit_breaker_middleware
   prometheus_middleware
   zipkin_middleware
   caching_middleware
   generic_middleware
