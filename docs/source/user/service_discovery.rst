Service Discovery
=================

While consuming a lot of different API, the problem to solve is to 
simplify the registration of services and its discoverability.

So the first approach is to have a static discovery, like we have
in the previous simple, but it means have a registry of services
in a configuration.
The :term:`service registry` may be commited in a tool like puppet,
but in case there is a lots of services, this does not scale, periodic
run of a puppet agent must run to discover new services.

To avoid the static inventory of service, tools may be used to handle
the :term:`service registry`, and build a :term:`client-side service discovery`
or a server-side discovery to have a dynamic approach.


Static Discovery
----------------

::

   from blacksmith import StaticDiscovery

   sd = StaticDiscovery(
       {
           ("gandi", "v5"): "https://api.gandi.net/v5/",
           ("github", None): "https://api.github.com/",
           ("sendinblue", "v3"): "https://api.sendinblue.com/v3/",
       }
   )


In that case we have a registry of public service.


.. note::

   Because those service does not use the same Authentication mechanism,
   this example is not really usefull.


Client Side Service Discovery
-----------------------------

Consul
~~~~~~

ConsulDiscovery is consuming the Consul API to fetch host that are
registered client side, this is a :term:`client-side service discovery`.

::

   from blacksmith import ConsulDiscovery

   # all parameters here are optional, the value
   # here are the defaults one for the example.
   sd = ConsulDiscovery(
      "http://consul:8500/v1",
      service_name_fmt="{service}-{version}",
      service_url_fmt="http://{address}:{port}/{version}",
      unversioned_service_name_fmt="{service}",
      unversioned_service_url_fmt="http://{address}:{port}",
      consul_token="abc",
   )


.. warning::

   Using consul in client require some discipline in naming convention,
   endoint must match pattern to build the rest endpoint. So every endpoint
   must follow the same pattern here.


.. note::

   **Take a look at the example!**

   https://github.com/mardiros/blacksmith/tree/master/examples/consul_sd



Server Side Service Discovery
-----------------------------

Router
~~~~~~

RouterDiscovery is calling every service behind a service gateway, a proxy,
that is connected to the :term:`service registry` to update is configuration.


::

   from blacksmith import RouterDiscovery

   sd = RouterDiscovery(
        service_url_fmt = "http://router/{service}/{version}",
        unversioned_service_url_fmt = "http://router/{service}",
   )

.. warning::

   Every endpoint must follow the same pattern here, it works well if the
   router configuration is based on a :term:`service registry`, but if the
   configuration of the router is maded by humans, inconcistency may exists,
   and the `Static Discovery` should be used instead.


.. note::

   **Take a look at the example!**

   https://github.com/mardiros/blacksmith/tree/master/examples/consul_template_sd

