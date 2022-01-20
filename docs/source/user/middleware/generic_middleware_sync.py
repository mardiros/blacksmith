from blacksmith import SyncHTTPMiddleware, SyncMiddleware
from blacksmith.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.typing import ClientName, Path


class SyncHTTPPrintMiddleware(SyncHTTPMiddleware):
    """Inject data in http query on every requests."""

    def __call__(self, next: SyncMiddleware) -> SyncMiddleware:
        def handle(
            req: HTTPRequest, client_name: ClientName, path: Path, timeout: HTTPTimeout
        ) -> HTTPResponse:
            print(f">>> {req}")
            resp = next(req, client_name, path, timeout)
            print(f"<<< {resp}")
            return resp

        return handle
