"""Cut the circuit in case a service is down."""

from collections.abc import Iterable

from purgatory import SyncAbstractUnitOfWork, SyncCircuitBreakerFactory
from purgatory.typing import TTL, Hook, Threshold

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.model.middleware.circuit_breaker import (
    PrometheusHook,
    exclude_httpx_4xx,
)
from blacksmith.domain.model.middleware.prometheus import PrometheusMetrics
from blacksmith.typing import ClientName, Path

from .base import SyncHTTPMiddleware, SyncMiddleware

Listeners = Iterable[Hook] | None


class SyncCircuitBreakerMiddleware(SyncHTTPMiddleware):
    """
    Prevent cascading failure.

    The circuit breaker is based on `purgatory`_, the middleware create
    one circuit breaker per client_name. The parameters are forwarded
    to all the clients. This middleware does not give the possibility to
    adapt a threshold or the time the circuit is opened per clients.

    .. _`purgatory`: https://pypi.org/project/purgatory-circuitbreaker/
    """

    def __init__(
        self,
        threshold: Threshold = 5,
        ttl: TTL = 30,
        listeners: Listeners = None,
        uow: SyncAbstractUnitOfWork | None = None,
        metrics: PrometheusMetrics | None = None,
    ):
        self.circuit_breaker = SyncCircuitBreakerFactory(
            default_threshold=threshold,
            default_ttl=ttl,
            exclude=[(HTTPError, exclude_httpx_4xx)],
            uow=uow,
        )
        if metrics:
            self.circuit_breaker.add_listener(PrometheusHook(metrics))
        if listeners:
            for listener in listeners:
                self.circuit_breaker.add_listener(listener)

    def initialize(self) -> None:
        self.circuit_breaker.initialize()

    def __call__(self, next: SyncMiddleware) -> SyncMiddleware:
        def handle(
            req: HTTPRequest,
            client_name: ClientName,
            path: Path,
            timeout: HTTPTimeout,
        ) -> HTTPResponse:
            with self.circuit_breaker.get_breaker(client_name):
                resp = next(req, client_name, path, timeout)
            return resp

        return handle
