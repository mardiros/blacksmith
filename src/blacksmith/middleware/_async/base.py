from typing import Any, Coroutine, Dict

from typing_extensions import Protocol

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse
from blacksmith.typing import ClientName, HttpMethod, Path


class AsyncMiddleware(Protocol):
    def __call__(
        self, req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
    ) -> Coroutine[Any, Any, HTTPResponse]:
        ...


class AsyncHTTPMiddleware:
    """Inject data in http query on every requests."""

    def __init__(self) -> None:
        pass

    async def initialize(self):
        pass

    def __call__(self, next: AsyncMiddleware) -> AsyncMiddleware:
        async def handle(
            req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
        ) -> HTTPResponse:
            return await next(req, method, client_name, path)

        return handle


class AsyncHTTPAddHeadersMiddleware(AsyncHTTPMiddleware):
    """Generic middleware that inject header."""

    headers: Dict[str, str]

    def __init__(self, headers: Dict[str, str]):
        self.headers = headers

    def __call__(self, next: AsyncMiddleware) -> AsyncMiddleware:
        async def handle(
            req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
        ) -> HTTPResponse:
            req.headers.update(self.headers)
            return await next(req, method, client_name, path)

        return handle