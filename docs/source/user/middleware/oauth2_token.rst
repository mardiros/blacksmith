OAuth2 Token's Middleware
=========================

This middleware allows to calls OAuth2 api using an access token,
using the Bearer scheme, using an OAuth2 Authorization Server.

Providing OAuth2 Authorization Server information, the access token
is retrieved and refreshed when needed automatically.

There is no storage backend involved here, the access token is stored
in RAM, and refreshed anytime needed. The client secrets and the
refresh token are providind in the constructor or by subclassing
and overriding the method :meth:`blacksmith.AsyncHTTPMiddleware.initialize` (
or :meth:`blacksmith.SyncHTTPMiddleware.initialize`).

Note that consuming middleware that requires an initialize requires
to call :meth:`blacksmith.AsyncClientFactory[Any].initialize` at the startup
of the application. For example by overriding the `lifespan` of a Starlette
application.
