Using Web Framework
===================

This page list plugings to get Web Framework integrations.

Django
------

The Django plugin `dj-blacksmith`_ is available and create and initialize clients
from the django settings. It support sync and async clients.

.. _`dj-blacksmith`: https://mardiros.github.io/dj-blacksmith/


Pyramid
-------

The plugin `pyramid-blacksmith`_ create a request property `blacksmith` that bind
blacksmith clients configured via the Pyramid configurator.

.. _`pyramid-blacksmith`: https://mardiros.github.io/pyramid-blacksmith/

FastAPI
-------

There is no plugins for FastAPI, but the example `unittesting`_ is based
on `FastAPI Dependency Injection`_.

.. _unittesting: https://github.com/mardiros/blacksmith/tree/main/examples/unit_testing/notif
.. _`FastAPI Dependency Injection`: https://fastapi.tiangolo.com/tutorial/dependencies/