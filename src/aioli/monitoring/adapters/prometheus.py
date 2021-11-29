"""Collect metrics based on prometheus."""
import pkg_resources
from typing import Any, Optional, TYPE_CHECKING
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
    `aioli_http_requests_total` Counter to get the number of http requests
    made.
    The counter `aioli_http_requests_total` as client_name, method, path and
    status_code labels.

    .. note::

        the service_name and service version is redundant with the client_name,
        so they are not exposed as labels. By the way, you may have multiple
        client_name for 1 service name/version.

    """

    def __init__(self, registry: Registry = None):
        from prometheus_client import Counter, Gauge, REGISTRY

        if registry is None:
            registry = REGISTRY
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

        self.aioli_http_requests = Counter(
            "aioli_http_requests",
            "number of http requests count.",
            registry=registry,
            labelnames=["client_name", "method", "path", "status_code"],
        )

    def inc_request(
        self,
        client_name: ClientName,
        method: HttpMethod,
        path: str,
        status_code: int,
    ):
        """
        Increment the prometheus counter `aioli_http_requests_total`.
        """
        self.aioli_http_requests.labels(client_name, method, path, status_code).inc()
