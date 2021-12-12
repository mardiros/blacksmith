Register resources
==================

A resource is a json document that is served by a :term:`service`
The example below, that has been copy paste from the test suite show
how to register a resource.


Full example of blacksmith regitration
---------------------------------

::

   import blacksmith
   from blacksmith import Request, Response, PathInfoField, PostBodyField, QueryStringField

   class SizeEnum(str, Enum):
      s = "S"
      m = "M"
      l = "L"


   class Item(Response):
      name: str = ""
      size: SizeEnum = SizeEnum.m


   class CreateItem(Request):
      name: str = PostBodyField()
      size: SizeEnum = PostBodyField(SizeEnum.m)


   class ListItem(Request):
      name: Optional[str] = QueryStringField(None)


   class GetItem(Request):
      item_name: str = PathInfoField()


   class UpdateItem(GetItem):
      name: Optional[str] = PostBodyField(None)
      size: Optional[SizeEnum] = PostBodyField(None)


   DeleteItem = GetItem

   blacksmith.register(
      "api",
      "item",
      "api",
      None,
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


Request parameters
------------------

The first things to do is to create models that represent every routes.

To represent a request parameter, the base class `Request` has to be overridden,
with special fields `HeaderField', `PathInfoField', `PostBodyField` or
`QueryStringField`.

For instance:

::

   class CreateItem(Request):
      name: str = PostBodyField()
      size: SizeEnum = PostBodyField(SizeEnum.m)


Response
--------

The response represent only the **json** body of a response.
When no schema is passed (explicitly None), then, the raw response is returned.

.. note::

   Note that for `collection_contract`, the response of the `"GET"` method,
   does not have to be a list. Elements of the list are validated by the schema
   one by one.
   This is the only schema that work like this.

::

   class Item(Response):
      name: str = ""
      size: SizeEnum = SizeEnum.m


.. note::

   Both Request and Response are :term:`Pydantic` models.
   So you can add all the Pydantic validation you want.


Registration
------------

The :term:`client_name` is the name to access to the :term:`resource` using the client factory.
Everytime the `client_name` is used, it must always match the same (:term:`service`, :term:`version`).
The resource will be a python property of that client that will be manipulable using methods.

This is a design decision to avoid to register client with service and version,
then resources. But the client name reprent an internal name for a service.

This may be usefull to register the same :term:`resource` of a service under different
client name by registering different parameter. The idea here is to register
a client for a specific usage and you may have different schema for that.

::

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

::

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

::

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

To keep the code clean, a good practice is to have a module named `resources`
and one submodule per services, then to have one submodule per per resources.

Something like this:

::

   mypkg/resources
   mypkg/resources/__init__.py
   mypkg/resources/serviceA/__init__.py
   mypkg/resources/serviceA/resourceA.py
   mypkg/resources/serviceA/resourceB.py
   mypkg/resources/serviceB/__init__.py
   mypkg/resources/serviceB/resourceC.py
   mypkg/resources/serviceB/resourceD.py


Then to load all the resources, use the `blacksmith.scan` method:


::

   import blacksmith

   # Fully load the registry with all resources
   aoili.scan("mypkg.resources")
