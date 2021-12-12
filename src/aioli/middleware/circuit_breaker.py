"""Cut the circuit in case a service is down."""
from datetime import timedelta
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    DefaultDict,
    Dict,
    Iterable,
    Optional,
    Type,
    Union,
    cast,
)

from aioli.domain.exceptions import HTTPError
from aioli.domain.model.http import HTTPRequest, HTTPResponse
from aioli.typing import ClientName, HttpMethod, Path

from .base import HTTPMiddleware, Middleware

if TYPE_CHECKING:
    try:
        from aiobreaker import CircuitBreaker as AioBreaker
        from aiobreaker import CircuitBreakerListener
        from aiobreaker.storage.base import CircuitBreakerStorage
    except ImportError:
        pass
    Listeners = Optional[Iterable["CircuitBreakerListener"]]
    StateStorage = Optional["CircuitBreakerStorage"]
    CircuitBreakers = Dict[str, "AioBreaker"]

else:
    Listeners = Any
    StateStorage = Any
    CircuitBreakers = Any


def exclude_httpx_4xx(exc):
    if isinstance(exc, HTTPError):
        err = cast(HTTPError, exc)
        return err.is_client_error
    return False


class CircuitBreaker(HTTPMiddleware):
    """
    Prevent the domino's effect using a circuit breaker.

    Requires to have the extra `circuit-breaker` installed.

    ::

        pip install aioli[circuit-breaker]

    """

    breakers: CircuitBreakers

    def __init__(
        self,
        fail_max=5,
        timeout_duration: Optional[timedelta] = None,
        listeners: Listeners = None,
        state_storage: StateStorage = None,
    ):
        import aiobreaker

        exclude = [exclude_httpx_4xx]

        self.CircuitBreaker = partial(
            aiobreaker.CircuitBreaker,
            fail_max=fail_max,
            timeout_duration=timeout_duration,
            exclude=exclude,
            listeners=listeners,
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
