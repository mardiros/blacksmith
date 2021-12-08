import abc

from aioli.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from aioli.typing import HttpMethod


class AbstractTransport(abc.ABC):
    @abc.abstractmethod
    async def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
        """Process the HTTP Get request."""
