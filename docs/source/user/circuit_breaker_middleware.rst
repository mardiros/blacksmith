Circuit Breaker Middleware
==========================

In microservices, the :term:`Circuit Breaker` is used to implement a
:term:`Fail Fast Model` to avoid :term:`cascading failure`.

The :term:`Circuit Breaker` is a middleware based on `aiobreaker`_ that
require an extra dependency.

.. _`aiobreaker`: https://pypi.org/project/aiobreaker/


Install it using the following command, using pip.

::

   pip install blacksmith[circuit-breaker]


..note::

   circuit-breaker is optional, but it is highly recommended to use it.


To use the circuit breaker, it must be added to the client factory
middleware stack.

::

   from time import timedelta

   from blacksmith import ClientFactory, CircuitBreaker, StaticDiscovery

   sd = StaticDiscovery({("api", None): "http://srv:8000/"})
   cli = ClientFactory(sd).add_middleware(
      CircuitBreaker(fail_max=5, timedelta(seconds=60))
   )


.. note::

   if `aiobreaker` is not install, an ImportError will be raised
   at the instanciation of the class `CircuitBreaker`.


The `CircuitBreaker` will affect all the clients, and in case one client,
identified by its :term:`client_name` failed more than the `fail_max`, during
an ellapsed time `timeout_duration` then all the incomming request will
automatically be rejected, throwing a `aiobreaker.state.CircuitBreakerError`.




Full example of the circuit_breaker
-----------------------------------

You will find an example using prometheus in the examples directory:

   https://github.com/mardiros/blacksmith/tree/master/examples/circuit_breaker
