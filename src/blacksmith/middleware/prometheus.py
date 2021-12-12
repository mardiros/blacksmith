"""Collect metrics based on prometheus."""
import time
from typing import TYPE_CHECKING, Any, Optional

import pkg_resources

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse
from blacksmith.typing import ClientName, HttpMethod, Path

from .base import HTTPMiddleware, Middleware

if TYPE_CHECKING:
    try:
        import prometheus_client
    except ImportError:
        pass
    Registry = Optional["prometheus_client.CollectorRegistry"]
else:
    Registry = Any


class PrometheusMetrics(HTTPMiddleware):
    """
    Collect the api calls made in a prometheus registry.

    It expose a `blacksmith_info` Gauge to get the blacksmith version, as a label, and a
    `blacksmith_request_latency_seconds_count` Counter to get the number of http requests
    made.
    The counter `blacksmith_request_latency_seconds_count` as client_name, method, path and
    status_code labels.

    .. note::

        the service_name and service version is redundant with the client_name,
        so they are not exposed as labels. By the way, you may have multiple
        client_name for 1 service name/version.

    """

    def __init__(self, buckets=None, registry: Registry = None):
        from prometheus_client import REGISTRY, Gauge, Histogram

        if registry is None:
            registry = REGISTRY
        if buckets is None:
            buckets = [0.05 * 2 ** x for x in range(10)]
        version_info = {
            "version": pkg_resources.get_distribution("blacksmith").version
        }
        self.blacksmith_info = Gauge(
            "blacksmith_info",
            "Blacksmith Information",
            registry=registry,
            labelnames=list(version_info.keys()),
        )
        self.blacksmith_info.labels(**version_info).set(1)

        self.blacksmith_request_latency_seconds = Histogram(
            "blacksmith_request_latency_seconds",
            "Latency of http requests in seconds",
            buckets=buckets,
            registry=registry,
            labelnames=["client_name", "method", "path", "status_code"],
        )

    def __call__(self, next: Middleware) -> Middleware:
        async def handle(
            req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
        ) -> HTTPResponse:
            status_code = 0
            start = time.perf_counter()
            try:
                resp = await next(req, method, client_name, path)
                status_code = resp.status_code
            except HTTPError as exc:
                status_code = exc.response.status_code
                raise exc
            finally:
                if status_code > 0:
                    latency = time.perf_counter() - start
                    self.blacksmith_request_latency_seconds.labels(
                        client_name, method, path, status_code
                    ).observe(latency)
            return resp

        return handle
