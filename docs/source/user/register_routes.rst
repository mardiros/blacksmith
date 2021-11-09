Register resources
==================

A resource is a json document that is served by a :term:`service`
The exemple below, that has been copy paste from the test suite show
how to register a resource.


::

   import aioli
   from aioli import Request, Response
   from aioli.domain.model import HTTPError, PathInfoField, PostBodyField, QueryStringField

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

   aioli.register(
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


Registration
------------

The :term:`client_name` is the name to access to the resource using the client factory.
Everytime the `client_name` is used, it must always match the same (:term:`service`, :term:`version`).

This is a design decision to avoid to register client with service and version,
then resources. But the client name reprent an internal name for a service.

This may be usefull to register the same route of a service under different
client name by registering different parameter. The idea here is to register
a client for a specific usage and you may have different schema for that.


::

   aioli.register(
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
