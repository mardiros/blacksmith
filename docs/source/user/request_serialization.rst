Alternative Request Serialization
=================================

Blacksmith has been designed to naturally supports JSON API.
Json is the standard in Rest Style API so it is the default
serialization.

But sometime you may want to supports alternative format.

Natively, Blacksmith supports ``application/json`` and
``application/x-www-form-urlencoded`` format.

To serialize a request in ``application/x-www-form-urlencoded``,
a header ``Content-Type`` can be added to the request model.
Blacksmith will serialize the body using a x-www-form-urlencoded
form.

.. literalinclude:: request_serialization_01.py


In the previous example, the fields foo and bar will be serialized in a
x-www-form-urlencoded form.

such as ``MyFormURLEncodedRequest(foo="foo", bar=42)`` will be
serialized to

::

   Content-Type: application/x-www-form-urlencoded

   foo=foo&bar=42


.. important::

   ``Content-Type`` here is **case sentitive**.


.. note::

   You may also note that the embeded urlencoded form version only supports flat
   structure, as is just a wrapper around the standar library function
   ``urllib.parse.urlencode``.



Registering serializer
----------------------

For extensibility, Blacksmith expose serialization are not a per client feature,
serializers are globals and register unsing the function
:func:`blacksmith.register_http_body_serializer`.

When a method serializer is added, it will have the highest priority of all the
serializers. You may use it to override the default Blacksmith serializer.

Now its time to add a dummy serializer.

.. literalinclude:: request_serialization_02.py

Now, if a request contains a `Content-Type` `text/xml+dummy` it will be serialized using
that serializer, and the body will always be `<foo/>`


.. important::

   If a request receive a ``Content-Type`` that is not handled by anyu serializer,
   an runtime exception ``UnregisteredContentTypeException`` will be raised during
   the serialization.
