Monitoring metrics
==================

Aioli can expose api calls metrics using :term:`Prometheus`.

It requires an extra dependency `prometheus_client` installed using the
following command.

::

   pip install aioli-client[prometheus]


To use the prometheus middlware, it has to be added to the `ClientFactory`.

::

   from aioli import ClientFactory, PrometheusMetrics, StaticDiscovery
   sd = StaticDiscovery({("api", None): "http://srv:8000/"})
   cli = ClientFactory(sd).add_middleware(PrometheusMetrics())


Metrics
-------

While installing the metrics collector, it will add metrics on api call
made.
There is `aioli_request_latency_seconds` Histogram and `aioli_info` Gauge.


aioli_request_latency_seconds Histogram
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Histogram have 3 metrics that are `aioli_request_latency_seconds_count`,
`aioli_request_latency_seconds_sum` and `aioli_request_latency_seconds_bucket`.

All those metrics are incremented on every API calls.


You may configure the buckets using the parameter buckets

::

   from aioli import PrometheusMetrics
   BUCKETS = [0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4, 12.8, 25.6]
   metric = PrometheusMetrics(buckets=BUCKETS)


`aioli_request_latency_seconds` labels are  `client_name`, `method`,
`path`, `status_code`.


.. note::

   The client_name can indicated the service at its version, and, because a
   service can register the same method/path many times, it can be usefull
   to get the monitoring on every binding.

   Imagine the same route is consumed to get different aspect of the resource
   in many place of a code base. It can be appropriate to register different
   clients to distingate them.


aioli_info Gauge
~~~~~~~~~~~~~~~~

The metrics is `aioli_info` which is a Gauge that always return 1, it is usefull
to get the version of the aioli client installed, in its label `version`.


Expose metrics
--------------

After collecting metrics in the registry, the metrics has to be exposed,
because aioli is a client purpose API, it does not offer a way to expose
them, but, usually, a web framework application is used for that,
and used scrapped by a Prometheus instanced.


Example using starlette
~~~~~~~~~~~~~~~~~~~~~~~

::

   from prometheus_client import (
      generate_latest, CONTENT_TYPE_LATEST, REGISTRY
   )
   from starlette.applications import Starlette
   from starlette.responses import Response

   app = Starlette()

   @app.route("/metrics", methods=["GET"])
   async def get_metrics(request):
      resp = Response(
         generate_latest(REGISTRY),
         media_type=CONTENT_TYPE_LATEST,
         )
      return resp


.. note::

   REGISTRY is the default registry, `PrometheusMetrics` can be 
   build by specifying another registry if necessary:

   ::

      from aioli import PrometheusMetrics
      metric = PrometheusMetrics(registry=my_registry)


Full example of prometheus metrics
----------------------------------

You will find an example using prometheus in the examples directory:

   https://github.com/mardiros/aioli/tree/master/examples/prometheus_metrics


.. figure:: ../screenshots/prometheus.png

   Example of querying the prometheus instance on http://prometheus.localhost/
