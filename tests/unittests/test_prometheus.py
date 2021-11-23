from prometheus_client import CollectorRegistry, REGISTRY

from aioli import __version__
from aioli.monitoring.adapters import PrometheusMetrics


def test_prom_metrics():
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    val = registry.get_sample_value("aioli_info", labels={"version": __version__})
    assert val == 1.0
    metrics.inc_request("client", "GET", "/", 200)
    val = registry.get_sample_value(
        "aioli_http_requests_total",
        labels={
            "client_name": "client",
            "method": "GET",
            "path": "/",
            "status_code": "200",
        },
    )
    assert val == 1
