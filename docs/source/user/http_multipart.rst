Attachment
==========

Blacksmith supports multiparts http query, in order to upload file.


Simple Request
--------------

Blacksmith will automatically handle query ``multipart/form-data``
instead of ``application/json`` if an attachment has been exposed
in the model.

In that case, http body field must be simple types.


.. literalinclude:: http_multipart_01.py

When a route will expose a route with this request model,
then, the serialized request will look like

::

   POST /upload HTTP/1.1
   Content-Type: multipart/form-data; boundary=5d3345920a8fae773a5f854d5895c397.

   --5d3345920a8fae773a5f854d5895c397
   Content-Disposition: form-data; name="foobar".

   FooBar

   --5d3345920a8fae773a5f854d5895c397

   Content-Disposition: form-data; name="attachmt"; filename="bar.xml".
   Content-Type: text/xml

   <ok/>

   --5d3345920a8fae773a5f854d5895c397--



Request with complex type
-------------------------

If a field contains a nested model, then it is a complex type,
and it will be serialized has json.

Example of schema:

.. literalinclude:: http_multipart_02.py


The request serialized version.

::

   POST /upload HTTP/1.1
   Content-Type: multipart/form-data; boundary=eadcb9ea7284fb51ae80bbcf28970770

   --eadcb9ea7284fb51ae80bbcf28970770
   Content-Disposition: form-data; name="query"

   {"name": "foo", "version": 42}

   --eadcb9ea7284fb51ae80bbcf28970770

   Content-Disposition: form-data; name="attachmt"; filename="bar.xml"
   Content-Type: text/xml

   <ok/>

   --eadcb9ea7284fb51ae80bbcf28970770--


.. note::

   The Content-Type application json is not set on the field.
