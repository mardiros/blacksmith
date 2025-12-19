5.0.1 - Released on 2025-12-19
------------------------------
* Internal http location has been updated to get swagger values.

5.0.0 - Released on 2025-12-13
------------------------------
* Drop support of python 3.9.
* Add support of python 3.14 (tested in the CI).
* Authorize union types in Response contract's schema.

4.1.2 - Released on 2025-11-07
------------------------------
* Fix usage of sequence in querystring, broken in 4.1.0.

4.1.1 - Released on 2025-04-10
------------------------------
* Fix complex type in post body field.

4.1.0 - Released on 2025-04-10
------------------------------
* Implement multipart form with attachment.
* Update the :class:`blacksmith.Response` model which is now
  an alias of pydantic ``BaseModel``.

4.0.5 - Released on 2025-01-29
------------------------------
* Fix usage of proxy.

4.0.4 - Released on 2025-01-07
------------------------------
* Release with httpx unfrozen.

4.0.3 - Released on 2025-01-07
------------------------------
* Fix serialization of HttpUrl for pydantic >2.9

4.0.2 - Released on 2024-11-28
------------------------------
* Release with httpx frozen to <0.28 due to Proxy update.

4.0.1 - Released on 2024-11-14
------------------------------
* Authorize older prometheus client library.

4.0.0 - Released on 2024-11-03
------------------------------
* Add :meth:`blacksmith.ResponseBox.inspect` method.
* Add :meth:`blacksmith.ResponseBox.inspect_err` method.
* Drop python 3.8 compatibility.
* Update the packaging (use uv and pdm instead of poetry).
* Update the CI.
* Change the licence to MIT License.

3.1.1 - Released on 2024-10-10
------------------------------
* Update the nomad service discovery for versionned service.
  Now the version is added in the environment variable by default.
  All the service and url are configurable.

3.1.0 - Released on 2024-09-05
------------------------------
* Add support of nomad for service discovery.
  See :class:`blacksmith.AsyncNomadDiscovery` - contrib from @gdchamal

3.0.0 - Released on 2024-06-23
------------------------------
* Drop support of python 3.7, add support of python 3.12
* Remove the deprecated result.response property replaced by result.unwrap()
* Drop support of pydantic 1

2.7.2 - Released on 2024-04-06
------------------------------
* Fix small typing issue

2.7.1 - Released on 2024-02-05
------------------------------
* Small fix for type Url with pydantic 2

2.7.0 - Released on 2024-01-21
------------------------------
* Add a way to support multiple serialization format, more than json.
  In this release, support of ``application/x-www-form-urlencoded`` is
  natively support. A new abstract class
  :class:`blacksmith.AbstractHttpBodySerializer` is available to handle
  new kind of serialization format.
  The function :func:`blacksmith.register_http_body_serializer` has been
  added to register new format.

2.6.1 - Released on 2024-01-11
------------------------------
* Add missing method :meth:`blacksmith.ResponseBox.unwrap_or_raise`

2.6.0 - Released on 2024-01-09
------------------------------
* Add support of Union types for request parameters

2.5.1 - Released on 2023-12-21
------------------------------
* Update httpx dependency for python > 3.7

2.5.0 - Released on 2023-12-20
------------------------------
* Add SecretStr support for parameters
* Update dependencies

2.4.1 - Released on 2023-10-24
------------------------------
* Update dependencies

2.4.0 - Released on 2023-07-29
------------------------------
* Add pydantic 2 support

note that pydantic 1 is still supported until blacksmith 3.0

2.3.3 - Released on 2023-07-29
------------------------------
* Update dependencies

2.3.2 - Released on 2023-05-11
------------------------------
* Remove aioredis, use redis.asyncio since it is deprecated
* Make it compat with python 3.11

2.3.1 - Released on 2023-03-14
------------------------------
* Do not override the content-type if it has already been set.

2.3.0 - Released on 2023-01-23
------------------------------
* Change behavior for explicit ``None`` in request parameters.
  Before this, it was not possible to properly choose attributes to patch to null.
  :ref:`See documentation<dealing_with_none>`

2.2.1 - Released on 2023-01-09
------------------------------
* Update dependencies (prometheus ^0.15)

2.2.0 - Released on 2023-01-03
------------------------------
* New method :meth:`blacksmith.ResponseBox.as_result`
  this method is usefull to cast an http response,
  to cast thes response box to a Result<ResponseSchema, ErrorFormat>
* Update dependency to at least pydantic 1.9

2.1.2 - Released on 2022-12-13
------------------------------
* Update dependency result to 0.9

2.1.1 - Released on 2022-11-15
------------------------------
* Fix consul service discovery support when ServiceAddress is empty.

2.1.0 - Released on 2022-10-11
------------------------------
* New method :meth:`blacksmith.ResponseBox.as_optional`
  This method is usefull for response that has no return
  schema and the response needs to be map to return something
  else without raising a
  :class:`blacksmith.domain.exceptions.NoResponseSchemaException`

2.0.0 - Released on 2022-10-11
------------------------------
* Fix concistency for :meth:`blacksmith.AsyncRouteProxy.collection_get` with
  other HTTP Response Object as using a result type from the
  :term:`result library`.

* Improve error handling. See :ref:`HTTP Errors`

Breaking Changes
~~~~~~~~~~~~~~~~

* The ``collection_get`` method in :class:`blacksmith.AsyncRouteProxy`
  and :class:`blacksmith.SyncRouteProxy` return a Result type instead of
  an iterator.

  ::

      api = await cli("api")

      # In blacksmith 1.0
      items: CollectionIterator[PartialItem] = await api.item.collection_get()

      # In blacksmith >=2.0
      items: Result[
         CollectionIterator[PartialItem], HTTPError
      ] = await api.item.collection_get()

  Note that the :class:`blacksmith.HTTPError` can be replaced by your own format,
  using the new parameter `error_parser` of the :class:`blacksmith.AsyncClientFactory`
  and :class:`blacksmith.SyncClientFactory`.

  See :ref:`HTTP Errors`

* The type of :class:`blacksmith.AsyncClientFactory`, :class:`blacksmith.AsyncClient`,
  :class:`blacksmith.SyncClientFactory` and :class:`blacksmith.SyncClient` cannot be
  used to specify collection and item types.

Deprecated
~~~~~~~~~~

* The :attr:`blacksmith.ResponseBox.response` is deprecated in favor of
  the :meth:`blacksmith.ResponseBox.unwrap` method.

  ::

      api = await cli("api")

      # In blacksmith 1.0
      item: Item = await api.item.get(Get(id=id)).response

      # In blacksmith >=2.0
      item: Item = await api.item.get(Get(id=id)).unwrap()
      # Or better
      result_item: ResponseBox[Item] = await api.item.get(Get(id=id))
      if result_item.is_ok():
         item = result_item.unwrap()  # unwrap will raise if the result is an error.
      else:
         error = result_item.unwrap_err()

  .. important::
     The :class:`blacksmith.ResponseBox` as plenty of new method to
     have the same mimic of the result type from the
     :term:`result library`.


1.0.2 - Released on 2022-06-02
------------------------------
* Update dependencies

1.0.1 - Released on 2022-02-27
------------------------------
* Update dependencies

1.0.0 - Released on 2022-02-12
------------------------------
* Add new page in the doc for the web framework integration
* Update dependencies

0.13.4 - Released on 2022-02-04
-------------------------------
* Update dependencies
* Add type support for prometheus
* Remove extra dependency `caching`, add `http_cache_async` and `http_cache_sync`.

0.13.3 - Released on 2022-01-29
-------------------------------
* Rename internal attribute request to read on :class:`blacksmith.HTTPTimeout`
* Declare missing type on :class:`blacksmith.AsyncAbstractTransport`

.. important::

   Breaking change

0.13.2 - Released on 2022-01-27
-------------------------------
* Exposing more classes in the main module:

  * CollectionParser
  * AsyncAbstractServiceDiscovery
  * SyncAbstractServiceDiscovery
  * AsyncAbstractTransport
  * SyncAbstractTransport
  * HTTPRequest
  * HTTPResponse

* Add an example on how to unit test.

0.13.1 - Released on 2022-01-24
-------------------------------
* Fix typo, rename AbtractTraceContext to :class:`blacksmith.AbstractTraceContext`

.. important::

   Breaking change

0.13.0 - Released on 2022-01-23
-------------------------------

.. important::

   This is the release candidate.
   Last releases where a lot about refactoring and fixing naming concistency.

   * No new feature will be added.
   * No major breaking change are going to be introduced.


* New feature

   * HTTP Cache Middleware now expose metrics using the its `metrics` argument.

* Breaking Changes

   * The :meth:`blacksmith.AsyncClientFactory.initialize` must be called to initialize
     middleware that requires it. (e.g. the ones that use a ``aioredis`` connections).
     See the documentation of :ref:`HTTP Cache Middleware` and
     :ref:`Circuit Breaker Middleware` for the detail.

   * All middleware classes ends with a ``Middleware`` suffix.
      * ``AsyncHTTPAuthorization`` => :class:`blacksmith.AsyncHTTPAuthorizationMiddleware`
      * ``AsyncHTTPBearerAuthorization`` => :class:`blacksmith.AsyncHTTPBearerMiddleware`
      * ``AsyncCircuitBreaker`` => :class:`blacksmith.AsyncCircuitBreakerMiddleware`
      * ``AsyncPrometheusMetrics`` => :class:`blacksmith.AsyncPrometheusMiddleware`
      * ``AsyncHTTPCachingMiddleware`` => :class:`blacksmith.AsyncHTTPCacheMiddleware`
      * ``SyncHTTPAuthorization`` => :class:`blacksmith.SyncHTTPAuthorizationMiddleware`
      * ``SyncHTTPBearerAuthorization`` => :class:`blacksmith.SyncHTTPBearerMiddleware`
      * ``SyncCircuitBreaker`` => :class:`blacksmith.SyncCircuitBreakerMiddleware`
      * ``SyncPrometheusMetrics`` => :class:`blacksmith.SyncPrometheusMiddleware`
      * ``SyncHTTPCachingMiddleware`` => :class:`blacksmith.SyncHTTPCacheMiddleware`

   * :class:`blacksmith.AsyncCircuitBreakerMiddleware` and
     :class:`blacksmith.SyncCircuitBreakerMiddleware` now have a
     :class:`blacksmith.PrometheusMetrics` instead of the prometheus middleware
     :class:`blacksmith.AsyncPrometheusMiddleware`
     or :class:`blacksmith.SyncPrometheusMiddleware`.

0.12.1 - Released on 2022-01-19
-------------------------------
* Expose AsyncClient and SyncClient for typing purpose.

0.12.0 - Released on 2022-01-19
-------------------------------
* Refactor transport to have the same signature as middleware.
* Breaking Change:
   * The http middleware does not have an http method
   * The type HttpMethod is not HTTPMethod
* The HTTPRequest type now have a method attribute.

0.11.0 - Released on 2022-01-15
-------------------------------
* Add typing support. see PEP 561
* Update the CI.
* Create a wrapper around json for the AbstractSerializer
  in the circuit breaker.

0.10.1 - Released on 2022-01-11
-------------------------------
* Add an AbstractCollectionParser to improve API signatures.
* Cleanup code, fix few typing issue and unmanage error on collection_get
  if the contract is not registered.

0.10.0 - Released on 2022-01-11
-------------------------------
* Add a method to have middleware per client.

0.9.2 - Released on 2022-01-07
------------------------------
* Fix typo in internals.

0.9.1 - Released on 2022-01-07
------------------------------
* Fix typo in documentations and internals.

0.9.0 - Released on 2022-01-07
------------------------------
* Add parameter proxies parameter in AsyncClientFactory and SyncClientFactory
   It allow to configure http proxies for http and https
* Add parameter verify_certificate parameter in AsyncClientFactory and SyncClientFactory
   It allow to disable the TLS Certificate check. By default, in case of invalid
   certificate, all request are rejected.

0.8.0 - Released on 2022-01-06
------------------------------
* Add support of the Sync version

..important:

   Breaking changes:

     * Rename all classes that do async with an ``Async`` prefix.
       * Services
       * Middlewares
       * Service Discovery

0.7.0 - Released on 2022-01-02
------------------------------
* Replace circuit breaker implementation.

..important:

   Breaking change in the middleware.

   Parameter fail_max is now named threshold
   Parameter timeout_duration is now named ttl and is a float (number of second).

0.6.3 - Released on 2021-12-29
------------------------------
* Expose the HTTPCachingMiddleware in blacksmith namespace

0.6.2 - Released on 2021-12-29
------------------------------
* Fix case sensitivity in cache header

0.6.1 - Released on 2021-12-29
------------------------------
* make http caching serializer in middleware configurable

0.6.0 - Released on 2021-12-29
------------------------------
* Add a http caching middleware based on redis
* Update zipkin integration for starlette-zipkin 0.2

0.5.0 - Released on 2021-12-13
------------------------------
* Reverse order of middleware to be natural and intuitive on insert

0.4.2 - Released on 2021-12-13
------------------------------
* Update httpx version ^0.21.1

0.4.1 - Released on 2021-12-12
------------------------------
* Collect circuit breaker metrics in prometheus

0.4.0 - Released on 2021-12-12
------------------------------
 * Rename project to blacksmith (prometheus metrics name updated too)
 * Implement middleware as a pattern to inject data in http request and response

    * Breaking changes: auth keyword is replace by middleware. (Documentation updated)
    * Breaking changes: auth keyword is replace by middleware. (Documentation updated)


0.3.0 - Released on 2021-12-08
------------------------------
 * Replace `aioli_http_requests` Gauge by `aioli_request_latency_seconds` Histogram. (prometheus)

0.2.1 - Released on 2021-12-05
------------------------------
 * Add metadata in pyproject.toml for pypi

0.2.0 - Released on 2021-12-05
------------------------------
 * Implement consul discovery (see consul example)
 * Implement router discovery (see consul template example)
 * Add prometheus metrics support
 * Add zipkin tracing support

0.1.0 - Released on 2021-11-14
------------------------------
 * Initial release
