.. _register_resources:

Register Resources
==================

A resource is a json document that is served by a :term:`service`
The example below, that has been copy paste from the test suite show
how to register a resource.


Full example of blacksmith regitration
--------------------------------------

.. literalinclude:: resources.py


Request parameters
------------------

The first things to do is to create models that represent every routes.

To represent a request parameter, the base class :class:`blacksmith.Request`
has to be overridden, with special fields 
:class:`blacksmith.HeaderField`,
:class:`blacksmith.PathInfoField`,
:class:`blacksmith.PostBodyField` or 
:class:`blacksmith.QueryStringField`.

For instance:

.. code-block::

   class CreateItem(Request):
      name: str = PostBodyField()
      size: SizeEnum = PostBodyField(SizeEnum.m)


Response
--------

The response represent only the **json body** of a response.
When no schema is passed (explicitly None), then, the raw response is returned.

.. note::

   Note that for ``collection_contract``, the response of the ``GET`` method,
   does not have to be a list. Elements of the list are validated by the schema
   one by one.
   This is the only difference between ``collection_contract`` and ``contract``,
   and it is the only schema that behave like this.

.. code-block::

   class Item(Response):
      name: str = ""
      size: SizeEnum = SizeEnum.m


.. note::

   Both Request and Response are :term:`Pydantic` models.
   So you can use all the Pydantic validation you want.


Registration
------------

The :term:`client_name` is the name to access to the :term:`resource` using the
client factory.
Everytime the client_name is used, it must always match the same 
(:term:`service`, :term:`version`) otherwise an exception will be raised
during the load of the application.

This is a design decision to avoid to register client with service and version,
then resources. But the client name reprent an internal name for a service.

By the way, sometime, it may be usefull to register the same :term:`resource`
of a service under different client_name by registering different parameter.
The idea here is to register a client for a specific usage and you may have
different schema for that.

Lastly, the resource will be accessible as a property of the client that will be
manipulable using methods where the Request define the parameter type of the
method, and the Response define the response type. 

.. code-block::

   blacksmith.register(
      client_name="api",
      resource="item",
      service="api",
      version=None,
      collection_path="/items",
      collection_contract={
         "GET": (ListItem, Item),
         "POST": (CreateItem, None),
      },
      path="/items/{item_name}",
      contract={
         "GET": (GetItem, Item),
         "PATCH": (UpdateItem, None),
         "DELETE": (DeleteItem, None),
      },
   )


Not that you can only declare the path and collection_path consumed.

This is completely valid to register only a single route.

.. code-block::

   blacksmith.register(
      client_name="api",
      resource="item",
      service="api",
      version="v1",
      path="/item",
      contract={
         "GET": (GetItem, Item),
      },
   )

or event a collection to bind an api that return a list.

.. code-block::

   blacksmith.register(
      client_name="api",
      resource="item",
      service="datastore",
      version="v1",
      path="/search",
      collection_contract={
         "GET": (SearchItem, Item),
      },
   )


.. note::

   An exception will be raised if a path or an http method has not
   been declared. No http request will be made.


Scanning resources
------------------

To keep the code clean, a good practice is to have a module named ``resources``
and one submodule per services, then to have one submodule per per resources.

Something like this:

.. code-block::

   mypkg/resources
   mypkg/resources/__init__.py
   mypkg/resources/serviceA/__init__.py
   mypkg/resources/serviceA/resourceA.py
   mypkg/resources/serviceA/resourceB.py
   mypkg/resources/serviceB/__init__.py
   mypkg/resources/serviceB/resourceC.py
   mypkg/resources/serviceB/resourceD.py


Then to load all the resources, use the :func:`blacksmith.scan` method:


.. code-block::

   import blacksmith

   # Fully load the registry with all resources
   blacksmith.scan("mypkg.resources")


.. important:: 

   There is no difference in the resources declaration for asynchronous
   and synchronous API.
   Resources declaration define what to consume, not how it will be consumed
   at the runtime.
