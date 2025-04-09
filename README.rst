Blacksmith
==========

.. image:: https://github.com/mardiros/blacksmith/actions/workflows/publish-doc.yml/badge.svg
   :target: https://mardiros.github.io/blacksmith/user/introduction.html
   :alt: Documentation

.. image:: https://github.com/mardiros/blacksmith/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/mardiros/blacksmith/actions/workflows/main.yml
   :alt: Continuous Integration

.. image:: https://codecov.io/gh/mardiros/blacksmith/branch/master/graph/badge.svg?token=17KAC0LW9H
   :target: https://codecov.io/gh/mardiros/blacksmith
   :alt: Coverage Report


Blacksmith is a library to build a solid microservices architecture based on REST API.

Todays, developers have lots of choices to create microservices,
plenty of framework are available, but when it comes to consume them,
there is a lack of clients.

Consuming an API is not just about doing HTTP requests, it has to be designed
for failure, monitoring, and service discovery with an elegant abstraction.
blacksmith aims to provide a solution for developers to write clean client code
and for ops to monitor api calls also on the client side.


What is Blacksmith
------------------

Blacksmith is a declarative tool for consuming REST Api.

In a REST API, resources are declared under HTTP routes, and every http verb
has its own definition.

In Blacksmith, every resources are bound to schemas that define request and response,
in order to abstract HTTP.

This is a common concept for SQL table with ORM, where tables are bound to models,
and then, operations are available on models. This is a usefull abstraction to
write maintainable code and to dive into a project easilly.

Handling API resources using an http client, such as `requests`_ does not handle
that abstraction, and does not handle bindings to objects, and can be compared to
a raw connection because it is just a transport.

This is the problem blacksmith is trying to solve, having a nice abstraction of
services that use REST in a microservices architecture.

.. note::

   | Blacksmith is not an HTTP Client or a model validator.
   | Blacksmith use `httpx`_ to perform http query, and use `Pydantic`_ to validate models.

.. _`requests`: https://docs.python-requests.org/
.. _`httpx`: https://www.python-httpx.org/
.. _`Pydantic`: https://pydantic-docs.helpmanual.io/


Why not using a SDK to consume APIs ?
-------------------------------------

SDK are about importing an external library in a service. And a service is
consumed by many services for different purpose. As a result, SDK create
coupling between service, and this is something that should be avoid.

An SDK for a service will declare all the resources, routes, and attribute
of resources when a service consumer may consume just a few.

SDK may hide what is really used by every service.

To avoid this, every consumers of API, should declare its own consumers
contracts to get a better view of which service use what.

.. note::

   TLDR; SDK are fine in public API, by the way, but not in a microservices
   architecture.


Building SDK
------------

By the way, blacksmith can be use to build a SDK for public API.


Working with or without asyncio
-------------------------------

Blacksmith is written for ``asyncio``, but works with synchronous API without overhead.
The synchronous API is generated using `unasync`_ and tested.

.. note::

   All class started by `Async` are asynchronous, and all class started by `Sync` are
   synchronous, for an explicit usage

.. _`unasync`: https://unasync.readthedocs.io/en/latest/


Read More
---------

You can read the `full documentation of this library here`_.

.. _`full documentation of this library here`: https://mardiros.github.io/blacksmith/user/introduction.html

.. important::

   | The documentation has been moved to github pages.
   | The documentation under readthedocs is obsolete.
