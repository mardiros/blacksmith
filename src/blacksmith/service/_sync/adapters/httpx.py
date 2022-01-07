import httpx
from httpx import Response as HttpxRepsonse
from httpx import Timeout as HttpxTimeout

from blacksmith.domain.exceptions import HTTPError, HTTPTimeoutError
from blacksmith.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.service.ports import SyncClient
from blacksmith.typing import HttpMethod

from ..base import SyncAbstractTransport


def safe_json(r: HttpxRepsonse):
    try:
        return r.json()
    except Exception:
        return {"error": r.text}


class SyncHttpxTransport(SyncAbstractTransport):
    """
    Transport implemented using `httpx`_.

    .. _`httpx`: https://www.python-httpx.org/

    """

    def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
        headers = request.headers.copy()
        if request.body:
            headers["Content-Type"] = "application/json"
        with SyncClient(verify=self.verify_certificate, proxies=self.proxies) as client:
            try:
                r = client.request(
                    method,
                    request.url,
                    params=request.querystring,
                    headers=headers,
                    content=request.body,
                    timeout=HttpxTimeout(timeout.request, connect=timeout.connect),
                )
            except httpx.TimeoutException as exc:
                raise HTTPTimeoutError(
                    f"{exc.__class__.__name__} while calling {method} {request.url}"
                )

        json = "" if r.status_code == 204 else safe_json(r)
        resp = HTTPResponse(r.status_code, r.headers, json=json)
        if not r.is_success:
            raise HTTPError(f"{r.status_code} {r.reason_phrase}", request, resp)
        return resp
