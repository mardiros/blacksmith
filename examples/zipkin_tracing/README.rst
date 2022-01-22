Example using Zipkin
====================

This example is a dummy microservice stack that send email to a user.

There is a "user" service which contains a users API used to retrieve fake email.

There is a "notification" api that take a username in parameter and a message
to send.

The "notification" service retrieve the "email" of the "user" and
send the message to the email address.


Requirements
------------

 * docker
 * docker-compose


Start the stack
---------------

docker-compose up


Call the service
----------------

::

   curl -H "Content-Type: application/json" \
      -v --data '{"username": "naruto", "message": "Datte Bayo"}' \
      -X POST http://notif.localhost/v1/notification


Check result
------------


The curl response contains a header `X-B3-Traceid` that can be searched

on http://jaeger.localhost/


.. image:: ./screenshots.png
