
from blacksmith import AsyncAbstractTransport, HTTPRequest, HTTPResponse, HTTPTimeout


class FakeTransport(AsyncAbstractTransport):
    def __init__(self, responses: dict[str, HTTPResponse]):
        super().__init__()
        self.responses = responses

    async def __call__(
        self,
        req: HTTPRequest,
        client_name: str,
        path: str,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        """This is the next function of the middleware."""
        return self.responses[f"{req.method} {req.url}"]
