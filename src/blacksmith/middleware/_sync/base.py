from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.typing import SyncMiddleware
from blacksmith.typing import ClientName, Path


class SyncHTTPMiddleware:
    """Inject data in http query on every requests."""

    def initialize(self) -> None:
        """
        Asynchronous initialization of a middleware.

        For instance, used to initialize connection to storage backend.
        """

    def __call__(self, next: SyncMiddleware) -> SyncMiddleware:
        def handle(
            req: HTTPRequest,
            client_name: ClientName,
            path: Path,
            timeout: HTTPTimeout,
        ) -> HTTPResponse:
            return next(req, client_name, path, timeout)

        return handle


class SyncHTTPAddHeadersMiddleware(SyncHTTPMiddleware):
    """
    Generic middleware that inject HTTP headers.

    :params: headers to inject in HTTP requests.
    """

    headers: dict[str, str]

    def __init__(self, headers: dict[str, str]):
        self.headers = headers

    def __call__(self, next: SyncMiddleware) -> SyncMiddleware:
        def handle(
            req: HTTPRequest,
            client_name: ClientName,
            path: Path,
            timeout: HTTPTimeout,
        ) -> HTTPResponse:
            req.headers.update(self.headers)
            return next(req, client_name, path, timeout)

        return handle
