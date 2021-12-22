"""Cut the circuit in case a service is down."""

from datetime import timedelta
from functools import partial
from typing import Dict, Iterable, List, Optional, cast

import aiobreaker
from aiobreaker import CircuitBreaker as AioBreaker
from aiobreaker import CircuitBreakerListener
from aiobreaker.state import CircuitBreakerBaseState, CircuitBreakerState
from aiobreaker.storage.base import CircuitBreakerStorage

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse
from blacksmith.typing import ClientName, HttpMethod, Path

from .base import HTTPMiddleware, Middleware
from .prometheus import PrometheusMetrics

Listeners = Optional[Iterable["CircuitBreakerListener"]]
StateStorage = Optional["CircuitBreakerStorage"]
CircuitBreakers = Dict[str, "AioBreaker"]


def exclude_httpx_4xx(exc):
    """Exclude client side http errors."""
    if isinstance(exc, HTTPError):
        err = cast(HTTPError, exc)
        return err.is_client_error
    return False


class GaugeStateValue:
    CLOSED = 0
    HALF_OPEN = 1
    OPEN = 2


class CircuitBreakerPrometheusListener(CircuitBreakerListener):
    def __init__(self, prometheus_metrics: PrometheusMetrics):
        self.prometheus_metrics = prometheus_metrics

    def failure(self, breaker: "AioBreaker", exception: Exception) -> None:
        self.prometheus_metrics.blacksmith_circuit_breaker_error.labels(
            breaker.name
        ).inc()

    def state_change(
        self,
        breaker: "AioBreaker",
        old: "CircuitBreakerBaseState",
        new: "CircuitBreakerBaseState",
    ) -> None:
        state = new.state
        if state == CircuitBreakerState.CLOSED:
            self.prometheus_metrics.blacksmith_circuit_breaker_state.labels(
                breaker.name
            ).set(GaugeStateValue.CLOSED)
        elif state == CircuitBreakerState.HALF_OPEN:
            self.prometheus_metrics.blacksmith_circuit_breaker_state.labels(
                breaker.name
            ).set(GaugeStateValue.HALF_OPEN)
        elif state == CircuitBreakerState.OPEN:
            self.prometheus_metrics.blacksmith_circuit_breaker_state.labels(
                breaker.name
            ).set(GaugeStateValue.OPEN)


class CircuitBreaker(HTTPMiddleware):
    """
    Prevent the domino's effect using a circuit breaker.

    Requires to have the extra `circuit-breaker` installed.

    ::

        pip install blacksmith[circuit-breaker]

    The circuit breaker is based on `aiobreaker`_, the middleware create
    one circuit breaker per client_name. The parameters ares forwarded
    to all the clients. This middleware does not give the possibility to
    adapt `fail_max` and `timeout_duration` per clients.

    .. _`aiobreaker`: https://pypi.org/project/aiobreaker/
    """

    breakers: CircuitBreakers

    def __init__(
        self,
        fail_max=5,
        timeout_duration: Optional[timedelta] = None,
        listeners: Listeners = None,
        state_storage: StateStorage = None,
        prometheus_metrics: Optional[PrometheusMetrics] = None,
    ):

        exclude = [exclude_httpx_4xx]
        cbllisteners: List["CircuitBreakerListener"] = (
            list(listeners) if listeners else []
        )
        if prometheus_metrics:
            cbllisteners.append(CircuitBreakerPrometheusListener(prometheus_metrics))

        self.CircuitBreaker = partial(
            aiobreaker.CircuitBreaker,
            fail_max=fail_max,
            timeout_duration=timeout_duration,
            exclude=exclude,
            listeners=cbllisteners,
            state_storage=state_storage,
        )
        self.breakers = {}

    def get_breaker(self, client_name: str) -> "AioBreaker":
        if client_name not in self.breakers:
            self.breakers[client_name] = self.CircuitBreaker(
                name=client_name,
            )
        return self.breakers[client_name]

    def __call__(self, next: Middleware) -> Middleware:
        async def handle(
            req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
        ) -> HTTPResponse:

            breaker = self.get_breaker(client_name)
            resp = await breaker.call_async(next, req, method, client_name, path)
            return cast(HTTPResponse, resp)

        return handle
