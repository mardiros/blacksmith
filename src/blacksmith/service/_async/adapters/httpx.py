from typing import Mapping, cast

from httpx import Timeout as HttpxTimeout
from httpx import TimeoutException

from blacksmith.domain.exceptions import HTTPError, HTTPTimeoutError
from blacksmith.domain.model import (
    HTTPRawResponse,
    HTTPRequest,
    HTTPResponse,
    HTTPTimeout,
)
from blacksmith.service.http_body_serializer import serialize_response
from blacksmith.service.ports import AsyncClient
from blacksmith.typing import ClientName, Path

from ..base import AsyncAbstractTransport


def build_headers(req: HTTPRequest) -> Mapping[str, str]:
    headers = req.headers.copy()
    if req.body and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    return headers


class AsyncHttpxTransport(AsyncAbstractTransport):
    """
    Transport implemented using `httpx`_.

    .. _`httpx`: https://www.python-httpx.org/

    """

    async def __call__(
        self,
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        headers = build_headers(req)
        async with AsyncClient(
            verify=self.verify_certificate,
            proxies=self.proxies,  # type: ignore
        ) as client:
            try:
                r = await client.request(  # type: ignore
                    req.method,
                    req.url,
                    params=req.querystring,
                    headers=headers,
                    content=req.body,
                    timeout=HttpxTimeout(timeout.read, connect=timeout.connect),
                )
            except TimeoutException as exc:
                raise HTTPTimeoutError(
                    f"{client_name} - {req.method} {path} - "
                    f"{exc.__class__.__name__} while calling {req.method} {req.url}"
                )

        resp = serialize_response(cast(HTTPRawResponse, r))
        if not r.is_success:
            raise HTTPError(
                f"{client_name} - {req.method} {path} - "
                f"{r.status_code} {r.reason_phrase}",
                req,
                resp,
            )
        return resp
