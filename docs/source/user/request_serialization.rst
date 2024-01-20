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