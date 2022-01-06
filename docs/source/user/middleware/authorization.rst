.. _`Authentication Middleware`:

Authentication Middleware
=========================

Service may require an authentication to authorize http requests.

The authentication part is not a part of the contract of a route,
but generally for a whole service or even for the whole registry.

For concistency, every service should use the same authorization
pattern.

With blacksmith, the authentication mechanism is declared in the
`AsyncClientFactory` to get the authentication working.
It also can be overridden on every api call.


Example
-------

.. literalinclude:: authorization_bearer.py

Create a custom authorization
-----------------------------

Imagine that you have an api that consume a basic authentication header.


.. literalinclude:: authorization_basic.py



Create a custom authentication based on http header
---------------------------------------------------

Imagine that you have an api that consume a "X-Secret" header to validate call.

.. literalinclude:: authorization_custom_header.py


Create a custom authentication based on querystring parameter
-------------------------------------------------------------

It is not recommended to pass server in a querystring, because
get parameter are oftenly logged by server, and secret should never
be logged. So blacksmith does not provide a middleware to handle this
query, but, you can still implementing it by yourself.

See how to implement it in the section :ref:`Generic Middleware`.
