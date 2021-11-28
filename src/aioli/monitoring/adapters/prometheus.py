"""Collect metrics to preometheus"""
import pkg_resources
from aioli.typing import ClientName, HttpMethod, ServiceName, Version

from ..base import AbstractMetricsCollector


class PrometheusMetrics(AbstractMetricsCollector):
    def __init__(self, registry=None):
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
        self.aioli_http_requests.labels(client_name, method, path, status_code).inc()
