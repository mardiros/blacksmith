Authorization
=============

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

   sd = ConsulDiscovery()
   # By default, every call will have a header
   # Authorization: Bearer {access_token}
   auth = HTTPAuthorization("Bearer", access_token)
   cli = ClientFactory(sd, auth=auth)
   api = await cli("api")
   protected_resource = await api.protected_resource.get({...})
   # example of overriden authentication
   # with no authentication
   public_resource = await api.public_resource.get(
       {}, auth=HTTPUnauthenticated()
   )



Create a custom authorization
-----------------------------

Imagine that you have an api that consume a basic authentication header.

::

   import base64
   from aioli.domain.model import HTTPAuthentication

   class BasicAuthorization(HTTPAuthentication):
       def __init__(self):
           b64head = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
           header = f"Basic {b64head}"
           return super().__init__(headers={"Authorization": header})

   auth = BasicAuthorization("me", "secret")
   cli = ClientFactory(sd, auth=auth)

