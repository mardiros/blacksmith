from httpx import AsyncClient
from httpx import Response as HttpxRepsonse

from aioli.domain.exceptions import HTTPError
from aioli.domain.model import HTTPRequest, HTTPResponse
from aioli.typing import HttpMethod

from ..base import AbstractTransport


def safe_json(r: HttpxRepsonse):
    try:
        return r.json()
    except Exception:
        return ""


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
        json = "" if r.status_code == 204 else safe_json(r)
        resp = HTTPResponse(r.status_code, json=json)
        if not r.is_success:
            raise HTTPError(f"{r.status_code} {r.reason_phrase}", request, resp)
        return resp
