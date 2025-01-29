from typing import Optional

from httpx import AsyncHTTPTransport

from blacksmith.domain.typing import AsyncMiddleware
from blacksmith.typing import Proxies


class AsyncAbstractTransport(AsyncMiddleware):
    verify_certificate: bool
    proxies: Optional[dict[str, AsyncHTTPTransport]]

    def __init__(
        self, verify_certificate: bool = True, proxies: Optional[Proxies] = None
    ):
        self.verify_certificate = verify_certificate
        self.proxies = (
            {key: AsyncHTTPTransport(proxy=val) for key, val in proxies.items()}
            if proxies
            else None
        )
