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

In the example above, the bearer token is share for every clients,
of the factory, which is ok for a service like prometheus where the
token is a configuration key, but most of the time, a token depends
on users.

So in the example below, we set the token only on a particular client.

.. literalinclude:: authorization_bearer2.py

In that example, we have a fake web framework that parse the authorization
header and expose the bearer token under a variable ``request.access_token``.
And we provide the middleware only for the execution ot that request.
 

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
