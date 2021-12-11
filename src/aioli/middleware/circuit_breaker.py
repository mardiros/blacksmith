"""Collect metrics based on prometheus."""
from datetime import timedelta
from typing import Any, Callable, Iterable, Optional, TYPE_CHECKING, Type, Union, cast


from aioli.domain.model.http import HTTPRequest, HTTPResponse

from aioli.typing import ClientName, HttpMethod, Path

from .base import HTTPMiddleware, Middleware

if TYPE_CHECKING:
    try:
        from aiobreaker import CircuitBreakerListener
        from aiobreaker.storage.base import CircuitBreakerStorage
    except ImportError:
        pass
    Listeners = Optional[Iterable["CircuitBreakerListener"]]
    StateStorage = Optional["CircuitBreakerStorage"]
else:
    Listeners = Any
    StateStorage = Any


class CircuitBreaker(HTTPMiddleware):
    """
    Prevent the domino's effect using a circuit breaker.

    Requires to have the extra `circuit-breaker` installed.

    ::

        pip install aioli[circuit-breaker]

    """

    def __init__(
        self,
        fail_max=5,
        timeout_duration: Optional[timedelta] = None,
        exclude: Optional[Iterable[Union[Callable, Type[Exception]]]] = None,
        listeners: Listeners = None,
        state_storage: StateStorage = None,
        name: Optional[str] = None,
    ):
        import aiobreaker

        self.breaker = aiobreaker.CircuitBreaker(
            fail_max=fail_max,
            timeout_duration=timeout_duration,
            exclude=exclude,
            listeners=listeners,
            state_storage=state_storage,
            name=name,
        )

    def __call__(self, next: Middleware) -> Middleware:
        async def handle(
            req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
        ) -> HTTPResponse:
            resp = await self.breaker.call_async(next, req, method, client_name, path)
            return cast(HTTPResponse, resp)

        return handle
