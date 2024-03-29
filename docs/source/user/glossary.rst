Glossary
========

.. glossary::

   Cache-Control
      The cache control is a response header of an http request defined by
      ``HTTP/1.1``. If contains caching directive used by browsers, CDN and any
      proxy that consume HTTP.
      https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control

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

      Source: https://en.wikipedia.org/wiki/Circuit_breaker_design_pattern

   client_name
      A **unique** name for your client. The client_name is the identifier of
      the client. It should be reuse in the resource declaration.

   client-side service discovery
      The :term:`service registry` is called by the client to find a host of a
      service.

   Consul
      | A software made to designed for service discovery.
      | Website: https://www.consul.io/

   Fail Fast Model
      In systems design, a fail-fast system is one which immediately reports at
      its interface any condition that is likely to indicate a failure.
      Fail-fast systems are usually designed to stop normal operation rather than
      attempt to continue a possibly flawed process.

   Prometheus
      | A software used for event monitoring and alerting.
      | Website: https://prometheus.io/

   Pydantic
      | Data validation using python type annotations.
      | Type hints provides user friendly errors when data is invalid.
      | Website: https://pydantic-docs.helpmanual.io/

   result library
      | A simple Result type for Python 3 inspired by Rust, fully type annotated.
      | Website: https://pypi.org/project/result/

   server-side service discovery
      The client is calling a proxy server that maintain its backends server
      list by receiving notification of the :term:`service registry` to maintain.

   service
      | A process that expose an API.
      | In Blacksmith, service are always REST HTTP API that serve Json documents.

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
      Sometime, services are versioned, the version can be declared as a separate
      parameter for readability.
      The version is None in case service does not expose a version number.

   whitesmith
      | A toolbox for testing the blacksmith client.
      | It generate skells to implement fake API consumed and pytest fixtures.
      | Website: https://github.com/mardiros/whitesmith

   resource
      A resource is a json document that is accessible and manipulable using
      http method.
