"""Cut the circuit in case a service is down."""

from collections.abc import Iterable

from purgatory import AsyncAbstractUnitOfWork, AsyncCircuitBreakerFactory
from purgatory.typing import TTL, Hook, Threshold

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.model.middleware.circuit_breaker import (
    PrometheusHook,
    exclude_httpx_4xx,
)
from blacksmith.domain.model.middleware.prometheus import PrometheusMetrics
from blacksmith.typing import ClientName, Path

from .base import AsyncHTTPMiddleware, AsyncMiddleware

Listeners = Iterable[Hook] | None


class AsyncCircuitBreakerMiddleware(AsyncHTTPMiddleware):
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
        uow: AsyncAbstractUnitOfWork | None = None,
        metrics: PrometheusMetrics | None = None,
    ):
        self.circuit_breaker = AsyncCircuitBreakerFactory(
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

    async def initialize(self) -> None:
        await self.circuit_breaker.initialize()

    def __call__(self, next: AsyncMiddleware) -> AsyncMiddleware:
        async def handle(
            req: HTTPRequest,
            client_name: ClientName,
            path: Path,
            timeout: HTTPTimeout,
        ) -> HTTPResponse:
            async with await self.circuit_breaker.get_breaker(client_name):
                resp = await next(req, client_name, path, timeout)
            return resp

        return handle
