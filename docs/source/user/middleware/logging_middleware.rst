Logging traffic using a Middleware
==================================

The logging middleware can be added to log the http traffic.

.. literalinclude:: logging_middleware.py


The logging can include the response body for debugging purpose,
this can be a security issue on production.

The log level DEBUG is required for that, and it can be disabled
event using the DEBUG log level.
