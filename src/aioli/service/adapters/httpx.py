from httpx import AsyncClient

from aioli.domain.model import HTTPRequest, HTTPResponse
from aioli.typing import HttpMethod


from ..base import AbstractTransport


class HttpxTransport(AbstractTransport):
    """
    Transport implemented using `httpx`_.

    .. _`httpx`: https://www.python-httpx.org/
    
    """
    async def request(self, method: HttpMethod, request: HTTPRequest) -> HTTPResponse:
        headers = request.headers.copy()
        if request.body:
            headers["Content-Type"] = "application/json"
        async with AsyncClient() as client:
            r = await client.request(
                method,
                request.url,
                params=request.querystring,
                headers=headers,
                content=request.body,
            )
        return HTTPResponse(r.status_code, json=r.json())
