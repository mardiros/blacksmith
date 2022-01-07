0.9.1 - Released at 2022-01-06
------------------------------
* Fix typo in documentations and internals

0.9.0 - Released at 2022-01-06
------------------------------
* Add parameter proxies parameter in AsyncClientFactory and SyncClientFactory
   It allow to configure http proxies for http and https
* Add parameter verify_certificate parameter in AsyncClientFactory and SyncClientFactory
   It allow to disable the TLS Certificate check. By default, in case of invalid
   certificate, all request are rejected.

0.8.0 - Released at 2022-01-06
------------------------------
* Add support of the Sync version

..important:

   Breaking changes:

     * Rename all classes that do async with an ``Async`` prefix.
       * Services
       * Middlewares
       * Service Discovery

0.7.0 - Released at 2022-01-02
------------------------------
* Replace circuit breaker implementation.

..important:

   Breaking change in the middleware.
  
   Parameter fail_max is now named threshold
   Parameter timeout_duration is now named ttl and is a float (number of second).

0.6.3 - Released at 2021-12-29
------------------------------
* Expose the HTTPCachingMiddleware in blacksmith namespace

0.6.2 - Released at 2021-12-29
------------------------------
* Fix case sensitivity in cache header

0.6.1 - Released at 2021-12-29
------------------------------
* make http caching serializer in middleware configurable

0.6.0 - Released at 2021-12-29
------------------------------
* Add a http caching middleware based on redis
* Update zipkin integration for starlette-zipkin 0.2

0.5.0 - Released at 2021-12-13
------------------------------
* Reverse order of middleware to be natural and intuitive on insert

0.4.2 - Released at 2021-12-13
------------------------------
* Update httpx version ^0.21.1

0.4.1 - Released at 2021-12-12
------------------------------
* Collect circuit breaker metrics in prometheus

0.4.0 - Released at 2021-12-12
------------------------------
 * Rename project to blacksmith (prometheus metrics name updated too)
 * Implement middleware as a pattern to inject data in http request and response

    * Breaking changes: auth keyword is replace by middleware. (Documentation updated)
    * Breaking changes: auth keyword is replace by middleware. (Documentation updated)


0.3.0 - Released at 2021-12-08
------------------------------
 * Replace `aioli_http_requests` Gauge by `aioli_request_latency_seconds` Histogram. (prometheus)

0.2.1 - Released at 2021-12-05
------------------------------
 * Add metadata in pyproject.toml for pypi

0.2.0 - Released at 2021-12-05
------------------------------
 * Implement consul discovery (see consul example)
 * Implement router discovery (see consul template example)
 * Add prometheus metrics support
 * Add zipkin tracing support

0.1.0 - Released at 2021-11-14
------------------------------
 * Initial release
