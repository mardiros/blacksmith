"""Collect metrics based on prometheus."""

import time
from typing import TYPE_CHECKING, Any

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.model.middleware.prometheus import PrometheusMetrics
from blacksmith.typing import ClientName, Path

from .base import SyncHTTPMiddleware, SyncMiddleware

if TYPE_CHECKING:
    try:
        import prometheus_client
    except ImportError:
        Regitry = Any
    else:
        Registry = prometheus_client.CollectorRegistry | None
else:
    Registry = Any


class SyncPrometheusMiddleware(SyncHTTPMiddleware):
    """
    Collect the api calls made in a prometheus registry.

    It expose a `blacksmith_info` Gauge to get the blacksmith version, as a label,
    and a `blacksmith_request_latency_seconds_count` Counter to get the number of
    http requests made.
    The counter `blacksmith_request_latency_seconds_count` as client_name, method,
    path and status_code labels.

    .. note::

        the service_name and service version is redundant with the client_name,
        so they are not exposed as labels. By the way, you may have multiple
        client_name for 1 service name/version.

    """

    metrics: PrometheusMetrics

    def __init__(self, metrics: PrometheusMetrics | None = None) -> None:
        self.metrics = metrics or PrometheusMetrics()

    def __call__(self, next: SyncMiddleware) -> SyncMiddleware:
        def handle(
            req: HTTPRequest,
            client_name: ClientName,
            path: Path,
            timeout: HTTPTimeout,
        ) -> HTTPResponse:
            status_code = 0
            start = time.perf_counter()
            try:
                resp = next(req, client_name, path, timeout)
                status_code = resp.status_code
            except HTTPError as exc:
                status_code = exc.response.status_code
                raise exc
            finally:
                if status_code > 0:
                    latency = time.perf_counter() - start
                    metric = self.metrics.blacksmith_request_latency_seconds
                    metric.labels(
                        client_name,
                        req.method,
                        path,
                        status_code,
                    ).observe(latency)
            return resp

        return handle
