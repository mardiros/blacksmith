from collections.abc import Coroutine
from typing import Any, Protocol

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.typing import ClientName, Path


class AsyncMiddleware(Protocol):
    """Signature of the middleware for the async version."""

    def __call__(
        self,
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> Coroutine[Any, Any, HTTPResponse]:
        """This is the next function of the middleware."""
        ...


class SyncMiddleware(Protocol):
    """Signature of the middleware for the sync version."""

    def __call__(
        self,
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        """This is the next function of the middleware."""
        ...
