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

Static Discovery Example
------------------------

Async
~~~~~

.. literalinclude:: sd_static_async.py

Sync
~~~~

.. literalinclude:: sd_static_sync.py

In that case we have a registry of public service.

.. note::

   Because those service does not share the same Authentication mechanism,
   this example is not really usefull.
   By the way, writin a custom :ref:`Authentication Middleware` can handle it.


Client Side Service Discovery
-----------------------------

Consul Example
~~~~~~~~~~~~~~

ConsulDiscovery is consuming the Consul API to fetch host that are
registered client side, this is a :term:`client-side service discovery`.


Async
~~~~~

.. literalinclude:: sd_consul_async.py

Sync
~~~~~

.. literalinclude:: sd_consul_sync.py


.. warning::

   Using consul in client require some discipline in naming convention,
   endoint must match pattern to build the rest endpoint. So every endpoint
   must follow the same pattern here.


.. note::

   **Take a look at the example!**

   https://github.com/mardiros/blacksmith/tree/master/examples/consul_sd


Nomad Example
~~~~~~~~~~~~~

When using Consul Connect in a Nomad cluster, upstreams declared in a jobspec
make available a mTLS connection on a `local_bind_port`. Addresses of these
services are injected as environment variables during deployment of the job.

Async
~~~~~

.. literalinclude:: sd_nomad_async.py

Sync
~~~~~

.. literalinclude:: sd_nomad_sync.py



Server Side Service Discovery
-----------------------------

Router Example
~~~~~~~~~~~~~~

RouterDiscovery is calling every service behind a service gateway, a proxy,
that is connected to the :term:`service registry` to update is configuration.


Async
~~~~~

.. literalinclude:: sd_router_async.py

Sync
~~~~~

.. literalinclude:: sd_router_sync.py


.. warning::

   Every endpoint must follow the same pattern here, it works well if the
   router configuration is based on a :term:`service registry`, but if the
   configuration of the router is maded by humans, inconcistency may exists,
   and the `Static Discovery` should be used instead.


.. note::

   **Take a look at the example!**

   https://github.com/mardiros/blacksmith/tree/master/examples/consul_template_sd
