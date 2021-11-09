Glossary
========

.. glossary::

   client_name
      A name for your client.

   service
      A process that expose an API. In Aioli, service are always REST HTTP API
      that serve Json documents.

   service discovery
      A service discovery is a mechanism to determin the endpoint of a service,
      in a rest api, it is basically a function that build an url prefix 
      from a :term:`service` and a :term:`version`.

   version
      Sometime, service are versioned, so you can declare the version as 
      a separate parameter for readability.
      The version may be None in case service does not expose a version number.

   resource
      A resource is a json document that is accessible and manipulable using
      http method.
