Authentication Middleware
=========================

Service may require an authentication to authorize http requests.

The authentication part is not a part of the contract of a route,
but generally for a whole service or even for the whole registry.

For concistency, every service should use the same authorization
pattern.

With aioli, the authentication mechanism is declared in the
`ClientFactory` to get the authentication working.
It also can be overridden on every api call.


Example
-------

::
   from aioli import ClientFactory, ConsulDiscovery, HTTPBearerAuthorization

   sd = ConsulDiscovery()
   # By default, every call will have a header
   # Authorization: Bearer {access_token}
   auth = HTTPBearerAuthorization(access_token)
   cli = ClientFactory(sd).add_middleware(auth)
   api = await cli("api")
   protected_resource = await api.protected_resource.get({...})


Create a custom authorization
-----------------------------


Imagine that you have an api that consume a basic authentication header.

::

   import base64
   from aioli.domain.model import HTTPAuthorization

   class BasicAuthorization(HTTPAuthorization):
       def __init__(self, username, password):
           b64head = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
           header = f"Basic {b64head}"
           return super().__init__("Basic", header)

   cli = ClientFactory(sd, auth=auth).add_middleware(BasicAuthorization("me", "secret"))


Create a custom authentication based on http header
---------------------------------------------------

Imagine that you have an api that consume a "X-Secret" header to validate call.

::

   import base64
   from aioli.domain.model import HTTPAddHeadersMiddleware

   class BasicAuthorization(HTTPAddHeadersMiddleware):
       def __init__(self, secret):
           return super().__init__(headers={"X-Secret": secret})

   auth = BasicAuthorization("me", "secret")
   cli = ClientFactory(sd, auth=auth)



Create a custom authentication based on querystring parameter
-------------------------------------------------------------

It is not recommended to pass server in a querystring, because
get parameter are oftenly logged by server, and secret should never
be logged. So aioli does not provide a middleware to handle this
query, but, you can still implementing it by yourself.

See how to implement it in the section :ref:`Generic Middleware`.
