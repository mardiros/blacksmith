Cache response in redis
=======================

This example is a dummy microservice stack that send email to a user.

There is a "user" service which contains a users API used to retrieve fake email.

There is a "notification" api that take a username in parameter and a message
to send.

The "notification" service retrieve the "email" of the "user" and
send the message to the email address.

The "user" service is slow and respond with a 'Cache-Control' header, and the notif service,
cache the reponse of the user using this amount of time.


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

   while true; do; curl -H "Content-Type: application/json" \
         -v --data '{"username": "naruto", "message": "Datte Bayo"}' \
         http://notif.localhost/v1/notification; done



http://prometheus.localhost/graph?g0.expr=blacksmith_request_latency_seconds_count&g0.tab=0&g0.stacked=1&g0.show_exemplars=0&g0.range_input=1h


Check result
------------

The mailbox is available in a web application http://mailhog.localhost/
to view the email has been properly received.
