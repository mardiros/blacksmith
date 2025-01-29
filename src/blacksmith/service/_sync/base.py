from typing import Optional

from httpx import HTTPTransport

from blacksmith.domain.typing import SyncMiddleware
from blacksmith.typing import Proxies


class SyncAbstractTransport(SyncMiddleware):
    verify_certificate: bool
    proxies: Optional[dict[str, HTTPTransport]]

    def __init__(
        self, verify_certificate: bool = True, proxies: Optional[Proxies] = None
    ):
        self.verify_certificate = verify_certificate
        self.proxies = (
            {key: HTTPTransport(proxy=val) for key, val in proxies.items()}
            if proxies
            else None
        )
