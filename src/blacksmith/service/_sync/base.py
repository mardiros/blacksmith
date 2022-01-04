import abc

from blacksmith.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.typing import HttpMethod


class SyncAbstractTransport(abc.ABC):
    @abc.abstractmethod
    def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
        """Process the HTTP Get request."""
