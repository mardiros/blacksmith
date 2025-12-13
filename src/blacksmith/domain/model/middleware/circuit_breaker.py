"""Cut the circuit in case a service is down."""

from collections.abc import Iterable
from typing import Any

from purgatory.typing import Hook

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model.middleware.prometheus import PrometheusMetrics

Listeners = Iterable[Hook] | None


def exclude_httpx_4xx(exc: HTTPError) -> bool:
    """Exclude client side http errors."""
    return exc.is_client_error


class GaugeStateValue:
    CLOSED = 0
    HALF_OPEN = 1
    OPEN = 2


class PrometheusHook:
    def __init__(self, metrics: PrometheusMetrics):
        self.metrics = metrics

    def __call__(self, circuit_name: str, evt_type: str, payload: Any) -> None:
        if evt_type == "state_changed":
            state = {
                "closed": GaugeStateValue.CLOSED,
                "half-opened": GaugeStateValue.HALF_OPEN,
                "opened": GaugeStateValue.OPEN,
            }[payload.state]
            metric = self.metrics.blacksmith_circuit_breaker_state
            metric.labels(circuit_name).set(state)
        elif evt_type == "failed":
            error_metric = self.metrics.blacksmith_circuit_breaker_error
            error_metric.labels(circuit_name).inc()
