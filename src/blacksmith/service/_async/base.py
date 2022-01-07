import abc

from blacksmith.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.typing import HttpMethod


class AsyncAbstractTransport(abc.ABC):

    def __init__(self, verify_verificate: bool = True):
        self.verify_verificate = verify_verificate

    @abc.abstractmethod
    async def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
        """Process the HTTP Get request."""
