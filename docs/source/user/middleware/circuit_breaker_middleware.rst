.. _`Circuit Breaker Middleware`:

Circuit Breaker Middleware
==========================

In microservices, the :term:`Circuit Breaker` is used to implement a
:term:`Fail Fast Model` to avoid :term:`cascading failure`.

The :term:`Circuit Breaker` is a middleware based on `purgatory`_.

.. _`purgatory`: https://pypi.org/project/purgatory-circuitbreaker/


.. note::

   circuit breaker is not installed by default,
   but it is highly recommended to use it.


To use the circuit breaker, it must be added to the client factory
middleware stack.

Async
~~~~~

.. literalinclude:: circuit_breaker_middleware_async.py

Sync
~~~~

.. literalinclude:: circuit_breaker_middleware_sync.py


The middleware create one circuit per client, identified by its
:term:`client_name`.
If alll consecutive call to routes of that clients happen more than
the ``threshold``, the circuit will be open for an ellapsed time `ttl` (in seconds).
When the cirtuit is open,  then all the incomming request will automatically
be rejected, throwing a `purgatory.OpenedState`.

.. note:: HTTPError 4xx are excluded by the circuit breaker.


By default, the circuits breaker states are stored in memory, but, it is
possible to share circuit breaker state using a redis server as a storage
backend.

To use a redis storage, a unit of work parameter is expected.


Async
~~~~~

.. literalinclude:: circuit_breaker_middleware_redis_async.py

Sync
~~~~

.. literalinclude:: circuit_breaker_middleware_redis_sync.py

.. note::

   | The circuit breaker state can also be monitored using prometheus.
   | Take a look at the full example for usage.


Full example of the circuit_breaker
-----------------------------------

You will find an example using prometheus and the circuit breaker in the examples directory:

   https://github.com/mardiros/blacksmith/tree/master/examples/circuit_breaker
