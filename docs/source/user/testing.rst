Writing tests with blacksmith
=============================

In software development, the testability of the code is the key of software
quality.

Using blacksmith, no mock are necessary to test the code. The correct way of
testing call is to implement an AbstractTransport (
:class:`blacksmith.AsyncAbstractTransport` or :class:`blacksmith.SyncAbstractTransport`)
with response the :class:`blacksmith.HTTPResponse`.

Implement a FakeTransport
~~~~~~~~~~~~~~~~~~~~~~~~~

The fake transport implementation has to be passed to the ``ClientFactory``
at the instantiation.

Using pytests the fake transport responses can be parametrized.

Example of fake transport:

.. literalinclude:: testing_01.py


Then, you need a dependency injection to properly initialize the client.

In the example below, we are injecting the transport in a FastAPI service.

.. literalinclude:: testing_02.py
   :emphasize-lines: 10

We can see that if a transport is passed in the setting, then it will be
used by the `get_client` method.

Now that we can bootstrap an application, then we can write the tests.

.. literalinclude:: ../../../examples/unittesting/notif/tests/test_views.py
   :emphasize-lines: 16-26

Then we can write the view that implement the notification sent.

.. literalinclude:: ../../../examples/unittesting/notif/src/notif/views.py
   :emphasize-lines: 12,15

The object ``AppConfig`` is retrieved by FastAPI using its dependency
injection, and the concigured ``get_client`` can be consumed directly.


Now to finalize our ``conftest.py``, some fixture must be written to.

::

   ...
   from notif.views import fastapi


   @pytest.fixture
   def settings():
      return {
         "service_url_fmt": "http://{service}.{version}",
         "unversioned_service_url_fmt": "http://{service}",
      }


   @pytest.fixture
   def configure_dependency_injection(params, settings):
      settings["transport"] = FakeTransport(params["blacksmith_responses"])
      FastConfig.configure(settings)


   @pytest.fixture
   def client(configure_dependency_injection):
      client = TestClient(fastapi)
      yield client


.. note::

   To finalize, we need to start the service for real, so we create
   an ``entrypoint.py`` file that will configure and serve the service.

   Here is an example with hypercorn.
   Note that the ``configure`` method is a couroutine in this example,
   but it was a simple method before, to simplify the example.

   .. literalinclude:: ../../../examples/unittesting/notif/src/notif/entrypoint.py


The full example can be found in the examples directory on github:

https://github.com/mardiros/blacksmith/tree/main/examples/unittesting/notif


Using whitesmith
~~~~~~~~~~~~~~~~

The :term:`whitesmith` package generate pytest fixture and handlers with fake
implementations, its at an early stage but can be a great way to create api
fixtures.

Usage:

.. code-block:: bash

   # install the deps ( use `pip install whitesmith` if you use pip)
   poetry add --group dev whitesmith
   poetry run whitesmith generate -m my_package.resources --out-dir tests/

This command generates a folder ``tests/whitesmith`` with a ``conftest.py``
and a ``tests/whitesmith/handlers`` containing fake api routes implemented
but that should be overriden for your needs.

Example:

.. code-block:: bash

   poetry run whitesmith generate -m tests
   Generating mocks from blacksmith registry...
   Processing client notif...
   Writing tests/whitesmith/handlers/notif.py

Check it out !
