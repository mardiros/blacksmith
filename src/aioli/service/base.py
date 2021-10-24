import abc


from aioli.domain.model import HTTPRequest, HTTPResponse
from aioli.typing import HttpMethod


class AbstractTransport(abc.ABC):
    @abc.abstractmethod
    async def request(self, method: HttpMethod, request: HTTPRequest) -> HTTPResponse:
        """Process the HTTP Get request."""
