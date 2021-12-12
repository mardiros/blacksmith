import abc

from blacksmith.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.typing import HttpMethod


class AbstractTransport(abc.ABC):
    @abc.abstractmethod
    async def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
        """Process the HTTP Get request."""
