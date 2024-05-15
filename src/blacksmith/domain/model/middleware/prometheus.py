"""Collect metrics based on prometheus."""

from importlib import metadata
from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    try:
        import prometheus_client
    except ImportError:
        pass
    Registry = Optional["prometheus_client.CollectorRegistry"]
else:
    Registry = Any


class PrometheusMetrics:
    def __init__(
        self,
        buckets: Optional[List[float]] = None,
        hit_cache_buckets: Optional[List[float]] = None,
        registry: Registry = None,
    ) -> None:
        from prometheus_client import REGISTRY, Counter, Gauge, Histogram

        if registry is None:
            registry = REGISTRY
        if buckets is None:
            buckets = [0.05 * 2**x for x in range(10)]
        if hit_cache_buckets is None:
            hit_cache_buckets = [0.005 * 2**x for x in range(10)]
        version_info = {"version": metadata.version("blacksmith")}
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

        self.blacksmith_circuit_breaker_error = Counter(
            "blacksmith_circuit_breaker_error",
            "Count the circuit breaker exception raised",
            registry=registry,
            labelnames=["client_name"],
        )

        self.blacksmith_circuit_breaker_state = Gauge(
            "blacksmith_circuit_breaker_state",
            "State of the circuit breaker. 0 is closed, 1 is half-opened, 2 is opened.",
            registry=registry,
            labelnames=["client_name"],
        )

        self.blacksmith_cache_hit = Counter(
            "blacksmith_cache_hit",
            "Request where the response has been retrieved from the cache.",
            registry=registry,
            labelnames=["client_name", "method", "path", "status_code"],
        )

        self.blacksmith_cache_miss = Counter(
            "blacksmith_cache_miss",
            "Request where the response has been retrieved from the cache.",
            registry=registry,
            labelnames=[
                "client_name",
                "cachable_state",
                "method",
                "path",
                "status_code",
            ],
        )

        self.blacksmith_cache_latency_seconds = Histogram(
            "blacksmith_cache_latency_seconds",
            "Latency of http cache middleware in seconds",
            buckets=hit_cache_buckets,
            registry=registry,
            labelnames=["client_name", "method", "path", "status_code"],
        )
