from typing import Any, Coroutine

from typing_extensions import Protocol

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse
from blacksmith.typing import ClientName, HttpMethod, Path


class AsyncMiddleware(Protocol):
    """Signature of the middleware for the async version."""

    def __call__(
        self, req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
    ) -> Coroutine[Any, Any, HTTPResponse]:
        """This is the next function of the middleware."""


class SyncMiddleware(Protocol):
    """Signature of the middleware for the sync version."""

    def __call__(
        self, req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
    ) -> HTTPResponse:
        """This is the next function of the middleware."""
