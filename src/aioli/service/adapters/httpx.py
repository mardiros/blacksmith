from httpx import AsyncClient

from aioli.domain.model import HTTPRequest, HTTPResponse
from aioli.typing import HttpMethod


from ..base import AbstractTransport


class HttpxTransport(AbstractTransport):
    async def request(self, method: HttpMethod, request: HTTPRequest) -> HTTPResponse:
        headers = request.header.copy()
        async with AsyncClient() as client:
            r = await client.request(
                method,
                request.url,
                params=request.querystring,
                headers=headers,
                json=request.body,
            )
        return HTTPResponse(r.status_code, json=r.json())
