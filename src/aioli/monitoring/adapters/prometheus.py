"""Collect metrics based on prometheus."""
from typing import TYPE_CHECKING, Any, Optional

import pkg_resources

from aioli.typing import ClientName, HttpMethod

from ..base import AbstractMetricsCollector

if TYPE_CHECKING:
    try:
        import prometheus_client
    except ImportError:
        pass
    Registry = Optional["prometheus_client.CollectorRegistry"]
else:
    Registry = Any


class PrometheusMetrics(AbstractMetricsCollector):
    """
    Collect the api calls made in a prometheus registry.

    It expose a `aioli_info` Gauge to get the aioli version, as a label, and a
    `aioli_request_latency_seconds_count` Counter to get the number of http requests
    made.
    The counter `aioli_request_latency_seconds_count` as client_name, method, path and
    status_code labels.

    .. note::

        the service_name and service version is redundant with the client_name,
        so they are not exposed as labels. By the way, you may have multiple
        client_name for 1 service name/version.

    """

    def __init__(self, buckets=None, registry: Registry = None):
        from prometheus_client import REGISTRY, Counter, Gauge, Histogram

        if registry is None:
            registry = REGISTRY
        if buckets is None:
            buckets = [0.05 * 2 ** x for x in range(10)]
        version_info = {
            "version": pkg_resources.get_distribution("aioli-client").version
        }
        self.aioli_info = Gauge(
            "aioli_info",
            "Aioli Information",
            registry=registry,
            labelnames=list(version_info.keys()),
        )
        self.aioli_info.labels(**version_info).set(1)

        self.aioli_request_latency_seconds = Histogram(
            "aioli_request_latency_seconds",
            "Latency of http requests in seconds",
            buckets=buckets,
            registry=registry,
            labelnames=["client_name", "method", "path", "status_code"],
        )

    def observe_request(
        self,
        client_name: ClientName,
        method: HttpMethod,
        path: str,
        status_code: int,
        latency: float,
    ):
        """
        Increment the prometheus counter `aioli_request_latency_seconds_count`.
        """
        self.aioli_request_latency_seconds.labels(
            client_name, method, path, status_code
        ).observe(latency)
