import asyncio
from collections.abc import Mapping
from typing import Any, cast

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
from blacksmith.service.ports import SyncClient
from blacksmith.typing import ClientName, Path, Proxies

from ..base import SyncAbstractTransport

ClientKey = tuple[asyncio.AbstractEventLoop | None, bool, tuple[tuple[str, str], ...]]


def build_headers(req: HTTPRequest) -> Mapping[str, str]:
    headers = req.headers.copy()
    if req.body and "Content-Type" not in headers and not req.attachments:
        headers["Content-Type"] = "application/json"
    return headers


class SyncHttpxTransport(SyncAbstractTransport):
    """
    Transport implemented using `httpx`_.

    .. _`httpx`: https://www.python-httpx.org/

    """

    client: SyncClient

    def __init__(self, verify_certificate: bool = True, proxies: Proxies | None = None):
        super().__init__(verify_certificate, proxies)

        self.client = SyncClient(verify=self.verify_certificate, mounts=self.proxies)

    def __call__(
        self,
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        headers = build_headers(req)

        try:
            kwargs: dict[str, Any] = (
                {"data": req.body, "files": req.attachments}
                if req.attachments
                else {"content": req.body}
            )
            r = self.client.request(  # type: ignore
                req.method,
                req.url,
                params=req.querystring,
                headers=headers,
                timeout=HttpxTimeout(timeout.read, connect=timeout.connect),
                **kwargs,
            )
        except TimeoutException as exc:
            raise HTTPTimeoutError(
                f"{client_name} - {req.method} {path} - "
                f"{exc.__class__.__name__} while calling {req.method} {req.url}"
            ) from exc

        resp = serialize_response(cast(HTTPRawResponse, r))
        if not r.is_success:
            raise HTTPError(
                f"{client_name} - {req.method} {path} - "
                f"{r.status_code} {r.reason_phrase}",
                req,
                resp,
            )
        return resp

    def close(self) -> None:
        self.client.close()
