Instanciating client
====================

After registrating resources in aioli, to consume API, a client must be
created. To create a client, service has to be discoverable using a
service discovery strategy, then resources can be consumed.

.. note::

   The :term:`service discovery` part will be covered later in the document,
   this chapter is about consuming resources.


To create a client in a simple way, a ClientFactory is an object responsible
to build client for every registrated resources.

::

   from aioli import ClientFactory, StaticDiscovery

   async def main():
       sd = StaticDiscovery({("api", None): "http://srv:8000/"})
       cli = ClientFactory(sd)
       api = await cli("api")
       items = await api.item.collection_get()


In the exemple above, we consume the previously registered resource `item`,
from the service "api" at version `None`.

The **item** property has method **collection_get**, **collection_post**,
**collection_put**, **collection_patch**, **collection_delete**,
**collection_options**, and **get**, **post**, **put**, **patch**,
**delete**, **options** in order to consume api routes.

.. important::

   Only registered routes works, consuming an unregistered route in the contract
   will raise error at the runtime.
