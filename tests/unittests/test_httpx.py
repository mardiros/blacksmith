from unittest import mock

import pytest
from httpx import Headers, Response
from httpx import TimeoutException as HttpxTimeoutException

from aioli.domain.exceptions import HTTPError
from aioli.domain.model import HTTPRequest, HTTPTimeout
from aioli.service.adapters.httpx import HttpxTransport

headers = Headers()
headers["Content-Type"] = "application/json"

dummy_json = {"name": "Alice"}
dummy_error = {"detail": "error"}
dummy_response = Response(200, headers=headers, json=dummy_json)
dummy_empty_response = Response(204, headers={}, json=None)
dummy_error_response = Response(422, headers={}, json=dummy_error)
dummy_error_500_response = Response(500, headers={}, text="internal server error")


def dummy_query_timeout():
    raise HttpxTimeoutException("ReadTimeout", request=None)


@mock.patch(
    "httpx._client.AsyncClient.request",
    return_value=dummy_response,
)
@pytest.mark.asyncio
async def test_query_http(patch):
    transport = HttpxTransport()
    resp = await transport.request("GET", HTTPRequest("/"), HTTPTimeout())
    assert resp.status_code == 200
    assert dict(resp.headers) == {
        "content-length": "17",
        "content-type": "application/json",
    }
    assert resp.json == dummy_json


@mock.patch(
    "httpx._client.AsyncClient.request",
    return_value=dummy_empty_response,
)
@pytest.mark.asyncio
async def test_query_http_204(patch):
    transport = HttpxTransport()
    resp = await transport.request("GET", HTTPRequest("/"), HTTPTimeout())
    assert resp.status_code == 204
    assert dict(resp.headers) == {}
    assert resp.json == ""


@mock.patch(
    "httpx._client.AsyncClient.request",
    return_value=dummy_error_response,
)
@pytest.mark.asyncio
async def test_query_http_422(patch):
    transport = HttpxTransport()
    with pytest.raises(HTTPError) as ctx:
        resp = await transport.request(
            "POST", HTTPRequest("/", body="{}"), HTTPTimeout()
        )

    assert str(ctx.value) == "422 Unprocessable Entity"
    assert ctx.value.status_code == 422
    assert ctx.value.json == dummy_error


@mock.patch(
    "httpx._client.AsyncClient.request",
    side_effect=lambda *args, **kwargs: dummy_query_timeout(),
)
@pytest.mark.asyncio
async def test_query_http_timeout(patch):
    transport = HttpxTransport()
    with pytest.raises(TimeoutError) as ctx:
        await transport.request("DELETE", HTTPRequest("/slow"), HTTPTimeout())
    assert str(ctx.value) == "TimeoutException while calling DELETE /slow"


@mock.patch(
    "httpx._client.AsyncClient.request",
    return_value=dummy_error_500_response,
)
@pytest.mark.asyncio
async def test_query_http_no_json(patch):
    transport = HttpxTransport()
    with pytest.raises(HTTPError) as ctx:
        resp = await transport.request(
            "POST", HTTPRequest("/", body="{}"), HTTPTimeout()
        )

    assert str(ctx.value) == "500 Internal Server Error"
    assert ctx.value.status_code == 500
    assert ctx.value.json == {"error": "internal server error"}
