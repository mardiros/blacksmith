Middlewares
===========

Blacksmith is extensible by adding middleware between the resource 
contracts and the real http query.

For example, requests may share a security secret that make not parts
of the contract of a route.

Middleware may be shared by all clients, such as prometheus middleware
that catch all the traffic for monitoring, or may be added on client
to add credentials per users.



.. note::

   Users can create their own middleware but blacksmith comes with its lists
   of usefull middlewares listed here.


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   circuit_breaker_middleware
   prometheus_middleware
   zipkin_middleware
   cache_middleware
   authorization
   generic_middleware
