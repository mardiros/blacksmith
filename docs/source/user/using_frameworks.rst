Using Web Framework
===================

This page list plugings to get Web Framework integrations.

Django
------

The Django plugin `dj-blacksmith`_ is available and create and initialize clients
from the django settings. It support sync and async clients.

.. _`dj-blacksmith`: https://dj-blacksmith.readthedocs.io/


Pyramid
-------

The plugin `pyramid-blacksmith`_ create a request property `blacksmith` that bind
blacksmith clients configured via the Pyramid configurator.

.. _`pyramid-blacksmith`: https://pyramid-blacksmith.readthedocs.io/

FastAPI
-------

There is no plugins for FastAPI, but the example `unittesting`_ is based
on `FastAPI Dependency Injection`_.

.. _unittesting: https://github.com/mardiros/blacksmith/tree/main/examples/unittesting/notif
.. _`FastAPI Dependency Injection`: https://fastapi.tiangolo.com/tutorial/dependencies/