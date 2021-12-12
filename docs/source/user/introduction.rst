Introduction
============

Blacksmith is a high level HTTP Client to consume REST APIs in json.

The aim of this library is to improve the design of application that
consume REST APIs in application. Every services are bound in client,
identified by a `client_name`, and every resources are named under
that client, and every routes are bound using contracts.

Contracts are a tuple of two schema that bind the HTTP Request, and
the HTTP Response using `pydantic`, so a strong typing improve the
readability, the writability and the robustnesss of your application,
with a better integration of the code in your editor.
