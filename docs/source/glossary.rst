Glossary
========

.. glossary::

   aiobreaker
      An asyncio library implement the :term:`Circuit Breaker` pattern.
      https://github.com/arlyon/aiobreaker

   cascading failure
      A cascading failure is a process in a system of interconnected parts in
      which the failure of one or few parts can trigger the failure of other
      parts and so on.
      https://en.wikipedia.org/wiki/Cascading_failure

   Circuit Breaker
      Design pattern used in software development.
      It is used to detect failures and encapsulates the logic of preventing
      a failure from constantly recurring, during maintenance, temporary
      external system failure or unexpected system difficulties. 
      https://en.wikipedia.org/wiki/Circuit_breaker_design_pattern

   client_name
      A name for your client.

   client-side service discovery
      The term:`service registry` is called by the client to find a host of a
      service.

   Consul
      A software made to designed for service discovery.
      Website: https://www.consul.io/

   Fail Fast Model
      In systems design, a fail-fast system is one which immediately reports at
      its interface any condition that is likely to indicate a failure.
      Fail-fast systems are usually designed to stop normal operation rather than
      attempt to continue a possibly flawed process.

   Prometheus
      A software used for event monitoring and alerting.
      https://prometheus.io/
   
   Pydantic
      Data validation using python type annotations.
      Type hints provides user friendly errors when data is invalid.
      https://pydantic-docs.helpmanual.io/

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
