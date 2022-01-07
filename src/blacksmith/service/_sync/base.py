import abc

from blacksmith.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.typing import HttpMethod, Proxies


class SyncAbstractTransport(abc.ABC):
    def __init__(self, verify_cerificate: bool = True, proxies: Proxies = None):
        self.verify_cerificate = verify_cerificate
        self.proxies = proxies

    @abc.abstractmethod
    def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
        """Process the HTTP Get request."""
