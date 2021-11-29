Glossary
========

.. glossary::

   client_name
      A name for your client.

   client-side service discovery
      The term:`service registry` is called by the client to find a host of a
      service.

   Consul
      A software made to designed for service discovery.
      Website: https://www.consul.io/

   Prometheus
      A software used for event monitoring and alerting.
      https://prometheus.io/

   server-side service discovery
      The client is calling a proxy server that maintain its backends server
      list by receiving notification of the term:`service registry` to maintain.

   service
      A process that expose an API. In Aioli, service are always REST HTTP API
      that serve Json documents.

   service discovery
      A service discovery is a mechanism to determin the endpoint of a service,
      in a rest api, it is basically a function that build an url prefix 
      from a :term:`service` and a :term:`version`.

   service registry
      The service registry is a catalog of known service that is maintained
      live. Sercice may anounce themselve in the service registry to get it
      up to date, or it may be done by a tier component. The service registry
      is a critical service that must be highly available.

   version
      Sometime, service are versioned, so you can declare the version as 
      a separate parameter for readability.
      The version may be None in case service does not expose a version number.

   resource
      A resource is a json document that is accessible and manipulable using
      http method.
