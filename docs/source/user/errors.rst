Dealing with errors
===================

.. note::

   This chapter describe common error that may happen at runtime.
   Some exception can happen during the registration phase, using 
   the function :func:`blacksmith.scan` which are not par not
   runtime desigated runtime errors here.

Timeout
-------

If a service is too slow, a :class:`blacksmith.HTTPTimeoutError` exception
will be raised to avoid a process to be locked.
The default timeout is at 30 seconds but it can be configured on the client
factory, and can be overriden on every http call.
The default connect timeout is at 15 seconds.

.. literalinclude:: errors_timeout.py

HTTP Errors
-----------

Blacksmith does not declare schema for errors.

It raised exceptions instead.

The exception raised is :class:`blacksmith.HTTPError` and get the
``status_code`` of the error.

.. note::

   Usually, a set of API share the same format for all the errors,
   but sometime, errors may also be html, so it is not possible to
   have a schema for errors.

The error is supposed to be a json document, under attribute ``json``.
If it is not the case, the content of the document will be in plain text
under the key ``detail``.


Opened Circuit Breaker
----------------------

While using the :ref:`Circuit Breaker Middleware`, the `OpenedState`_ exception is
raised from the `Circuit Breaker library`_, when a service is detected down,
and then, that circuit has been opened.

.. _`OpenedState`: https://purgatory.readthedocs.io/en/latest/develop/domain/model.html#purgatory.domain.model.OpenedState
.. _`Circuit Breaker library`: https://purgatory.readthedocs.io/
