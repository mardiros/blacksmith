Dealing with errors
===================

Timeout
-------

If a service is too slow, an exception will be raised to avoid a process
to be locked.
The default timeout is at 30 seconds but it can be configured on the client
factory, and can be overriden on every http call.


::

   from aioli.domain.exception import HTTPTimeout

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
   # Or even
   resources = await api.resource.collection_get(timeout=(42.0, 7.0))
