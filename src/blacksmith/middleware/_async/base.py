from typing import Dict

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.typing import AsyncMiddleware
from blacksmith.typing import ClientName, Path


class AsyncHTTPMiddleware:
    """Inject data in http query on every requests."""

    def __init__(self) -> None:
        pass

    async def initialize(self) -> None:
        pass

    def __call__(self, next: AsyncMiddleware) -> AsyncMiddleware:
        async def handle(
            req: HTTPRequest,
            client_name: ClientName,
            path: Path,
            timeout: HTTPTimeout,
        ) -> HTTPResponse:
            return await next(req, client_name, path, timeout)

        return handle


class AsyncHTTPAddHeadersMiddleware(AsyncHTTPMiddleware):
    """
    Generic middleware that inject HTTP headers.

    :params: headers to inject in HTTP requests.
    """

    headers: Dict[str, str]

    def __init__(self, headers: Dict[str, str]):
        self.headers = headers

    def __call__(self, next: AsyncMiddleware) -> AsyncMiddleware:
        async def handle(
            req: HTTPRequest,
            client_name: ClientName,
            path: Path,
            timeout: HTTPTimeout,
        ) -> HTTPResponse:
            req.headers.update(self.headers)
            return await next(req, client_name, path, timeout)

        return handle
