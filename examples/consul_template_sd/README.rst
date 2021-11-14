Example using Consul Template
=============================

This example is a dummy microservice stack that do nothing.

This is a copy/paste of the consul_sd service, and we adapt it
to use a `RouterDiscovery` to get a Server-Side Discovery
architecture.


Call the service
----------------

::

   curl -H "Content-Type: application/json" \
      --data '{"username": "naruto", "message": "Datte Bayo"}' \
      -X POST http://router.localhost/notif-v1/v1/notification


Check result
------------

The mailbox is available in a web application http://mailhog.localhost/
to view the email has been properly received.
