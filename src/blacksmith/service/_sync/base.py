from typing import Optional

from blacksmith.domain.typing import SyncMiddleware
from blacksmith.typing import Proxies


class SyncAbstractTransport(SyncMiddleware):
    def __init__(
        self, verify_certificate: bool = True, proxies: Optional[Proxies] = None
    ):
        self.verify_certificate = verify_certificate
        self.proxies = proxies
