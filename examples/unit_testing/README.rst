Unit testing with blacksmith
============================

This example show how to improve the testability of software that use blacksmith.


This is a copy of the consul_sd example, but with some replacement of component
in the ``notif`` service to improve the testability.

It use ``FastAPI`` instead of ``Starlette``, and user ``hypercorn`` instead of
``uvicorn``.

``FastAPI`` is preferred for its dependency injection and ``hypercorn`` for its
configuration.
