from blacksmith import SyncHTTPMiddleware, SyncMiddleware
from blacksmith.domain.model import HTTPRequest, HTTPResponse
from blacksmith.typing import ClientName, HTTPMethod, Path


class SyncHTTPPrintMiddleware(SyncHTTPMiddleware):
    """Inject data in http query on every requests."""

    def __call__(self, next: SyncMiddleware) -> SyncMiddleware:
        def handle(
            req: HTTPRequest, method: HTTPMethod, client_name: ClientName, path: Path
        ) -> HTTPResponse:
            print(f">>> {req}")
            resp = next(req, method, client_name, path)
            print(f"<<< {resp}")
            return resp

        return handle
