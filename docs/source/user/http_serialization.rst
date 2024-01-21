Alternative Serialization
=========================

Blacksmith has been designed to naturally supports JSON API.
Json is the standard in Rest Style API so it is the default
serialization.

But sometime you may want to supports alternative document format.

Natively, Blacksmith supports ``application/json`` and
``application/x-www-form-urlencoded`` format.

Request
-------

To serialize a request in ``application/x-www-form-urlencoded``,
a header ``Content-Type`` can be added to the request model.
Blacksmith will serialize the body using a x-www-form-urlencoded
form.

.. literalinclude:: http_serialization_01.py


In the previous example, the fields foo and bar will be serialized in a
x-www-form-urlencoded form.

such as ``MyFormURLEncodedRequest(foo="foo", bar=42)`` will be
serialized to

::

   Content-Type: application/x-www-form-urlencoded

   foo=foo&bar=42


.. important::

   In the request model, ``Content-Type`` is **case sentitive**.


.. note::

   You may also note that the embeded urlencoded form version only supports flat
   structure, as is just a wrapper around the standard library function
   ``urllib.parse.urlencode``.


Response
--------

While serializing the response, the ``Content-Type`` header is also used
to serialize the response body. And, if the response omit it, Blacksmith will
assume it is a Json document. Usually posting for using
``application/x-www-form-urlencoded`` will not generate a response in this format
but the internet is full of surprise!


Registering a new serializer
----------------------------

For extensibility, Blacksmith expose serialization are not a per client feature,
serializers are globals and register unsing the function
:func:`blacksmith.register_http_body_serializer`.

When a method serializer is added, it will have the highest priority of all the
serializers. You may use it to override the default Blacksmith serializer.

Now its time to add a dummy serializer.

.. literalinclude:: http_serialization_02.py

Now, if a request contains a `Content-Type` `text/xml+dummy` it will be serialized using
that serializer, and the body will always be `<foo/>`


.. important::

   If a request receive a ``Content-Type`` that is not handled by any serializer,
   an runtime exception ``UnregisteredContentTypeException`` will be raised during
   the serialization.


the serializer implement a method
:meth:`blacksmith.AbstractHttpBodySerializer.deserialize` to handle responses
deserialization.

If you request is talking to a specific request body, there is chance that the API
respond in a similar format too, this is where the
:meth:`blacksmith.AbstractHttpBodySerializer.deserialize` will be used.
