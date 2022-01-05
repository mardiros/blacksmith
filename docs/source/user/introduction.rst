Introduction
============

Blacksmith is a high level HTTP Client to consume json REST APIs.

The aim of this library is to improve the design of application that consume
REST APIs.
Every services are bound in clients. A client is identified by its
:term:`client_name`, and every resources under that client are defined using
contracts for every routes the application consume.

Contracts are a tuple of two schema that bind the HTTP Request, and
the HTTP Response using :term:`pydantic`.

As a result, it enforce the typing that improve the readability,
the writability and the robustnesss of applications, with a better
integration of the code in text editors.

Blacksmith provide an asynchronous API to works with asyncio, and also
a synchronous API.