Dealing with errors
===================

.. note::

   This chapter describe common error that may happen at runtime.
   Some exception can happen during the registration phase, using
   the function :func:`blacksmith.scan` which are not par not
   runtime desigated runtime errors here.

HTTP Errors
-----------

.. versionchanged:: 2.0

   the HTTP Errors are not throws anymore.

When a resource is consuming a get, post, put, patch, delete, collection_get,
and so on, the function return a Result object that have method to unwrap
the resource or the associated error.

An error is a class :class:`blacksmith.HTTPError` and get the ``status_code``
of the errors with a JSON payload.


Async example
~~~~~~~~~~~~~

.. literalinclude:: errors_01.py

Sync example
~~~~~~~~~~~~

.. literalinclude:: errors_02.py



.. note::

   Blacksmith does not declare schema for errors.
   It could be an improvement in the future.

   Usually, a set of API share the same format for all the errors,
   but sometime, errors may also be html, so it is not possible to
   have a schema for errors.

The error is supposed to be a json document, under attribute ``json``.
If it is not the case, the content of the document will be in plain text
under the key ``detail``.


Timeout
-------

If a service is too slow, a :class:`blacksmith.HTTPTimeoutError` exception
will be raised to avoid a process to be locked.
The default timeout is at 30 seconds but it can be configured on the client
factory, and can be overriden on every http call.
The default connect timeout is at 15 seconds.

.. literalinclude:: errors_timeout.py


Opened Circuit Breaker
----------------------

While using the :ref:`Circuit Breaker Middleware`, the `OpenedState`_ exception is
raised from the `Circuit Breaker library`_, when a service is detected down,
and then, that circuit has been opened.

.. _`OpenedState`: https://purgatory.readthedocs.io/en/latest/develop/domain/model.html#purgatory.domain.model.OpenedState
.. _`Circuit Breaker library`: https://purgatory.readthedocs.io/
