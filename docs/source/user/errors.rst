Dealing with errors
===================

Timeout
-------

If a service is too slow, an exception will be raised to avoid a process
to be locked.
The default timeout is at 30 seconds but it can be configured on the client
factory, and can be overriden on every http call.
The default connect timeout is at 15 seconds.

::

   from blacksmith.domain.exception import HTTPTimeout

   # read timeout at 5 seconds
   # and connect timeout at 5 seconds
   cli = ClientFactory(sd, timeout=(10.0,5.0))
   # Or
   cli = ClientFactory(sd, timeout=HTTPTimeout(10.0, 5.0))

   # All timeout at 10 seconds
   cli = ClientFactory(sd, timeout=10.0)
   # Or
   cli = ClientFactory(sd, timeout=HTTPTimeout(10.0))


   api = await cli("api")

   # user the default timeout
   resources = await api.resource.collection_get()

   # force the timeout
   resources = await api.resource.collection_get(timeout=42.0)
   # Or even with a connect timeout
   resources = await api.resource.collection_get(timeout=(42.0, 7.0))


Raised Exceptions
-----------------

Blacksmith does not declare schema for errors. It raised exceptions instead.
The exception raised is `HTTPError` and get the `status_code` of the 
error. The error is supposed to be a json document, under attribute `json`.
If it is not the case, the content of the document will be in plain text under the key "detail".

While using the :ref:`Circuit Breaker`, the CircuitBreakerError exception is
raised when a service is down, and the circuit has been opened.