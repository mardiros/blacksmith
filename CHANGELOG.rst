0.4.0 - Released at 2021-12-12
------------------------------
 * Rename project to blacksmith (prometheus metrics name updated too)
 * Implement middleware as a pattern to inject data in http request and response.

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
