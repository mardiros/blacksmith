from httpx import AsyncHTTPTransport

from blacksmith.domain.typing import AsyncMiddleware
from blacksmith.typing import Proxies


class AsyncAbstractTransport(AsyncMiddleware):
    verify_certificate: bool
    proxies: dict[str, AsyncHTTPTransport] | None

    def __init__(self, verify_certificate: bool = True, proxies: Proxies | None = None):
        self.verify_certificate = verify_certificate
        self.proxies = (
            {key: AsyncHTTPTransport(proxy=val) for key, val in proxies.items()}
            if proxies
            else None
        )
