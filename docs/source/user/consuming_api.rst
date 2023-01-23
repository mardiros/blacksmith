Consuming API
=============

Now the :ref:`client has been instanciated<instanciating_clients>`,
:ref:`registered resources<register_resources>` can be consumed.

Consume what is registered
~~~~~~~~~~~~~~~~~~~~~~~~~~

Reusing the previously registered resource below, an instanciated client
can consume only the registered route of that resource.

.. literalinclude:: register_routes_02.py

It means that here that che client can consume the **collection_get** and
the **get** method of the resource. The typing system will proposed other
methods, such as **post** but the ``"POST"`` schema has not been regitered,
and will raise an error.

In REST, the ``~`` is widely used to do a like operator, to produce a
querystring such as `?~name=...`, the parameter ``SearchItem`` as below:

.. code-block::

   items = await cli.item.collection_get({"~name": "..."})


.. note::

   The kwargs syntax ``SearchItem(**{"~name": "..."})`` can also be used.


Using default
~~~~~~~~~~~~~

All fields may use a default or a default factory that are serialized in http request.

.. code-block::

   class Dummy(Request):
      x_message_type: str = HeaderField(default="Foo", alias="X-Message-Type")
      created_at: float = PostBodyField(default_factory=time.time, alias="X-Timestamp")

In this code, the header ``X-Timestamp`` will contains float of, ``time.time()`` result.
And the `X-Message-Type` is sent with foo.

Dealing with null values
~~~~~~~~~~~~~~~~~~~~~~~~

Lots of api will use an explicit null to patch a resource, and missing values
are not patched at all. In blacksmith, explicit ``None`` are converted with
null, but implicit ``None`` are not serialized to http request.

See example below:

.. code-block::

   class PatchDummy(Request):
      name: str = PathInfoField()
      state: Optional[str] = PostBodyField()
      country: Optional[str] = PostBodyField()

   blacksmith.register(
      client_name="api",
      resource="dummy",
      service="api",
      version="v1",
      path="/dummies/{name}",
      contract={
         "PATCH": (PatchDummy, None),
      },
   )

   sd = SyncStaticDiscovery({("api", None): "http://srv:8000/"})
   cli = SyncClientFactory(sd)
   api = cli("api")

   # this call api call will patch the state to `null`
   # but the ``country`` is not send in the request.

   api.patch({"name": "foo", "state": None})


.. important::

   Default values are always sent, so imagine the following example

   .. code-block::

      class PatchDummy(Request):
         name: str = PathInfoField()
         state: Optional[str] = PostBodyField()
         country: Optional[str] = PostBodyField(default="FR")

   In that case, the **PATCH** will always sent a default country.

   ``api.patch({"name": "foo", "state": None, "country": None})`` will
   sent a ``None`` value for country.

   **default values has to be used sparingly**.
