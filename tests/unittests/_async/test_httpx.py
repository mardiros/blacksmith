from typing import Any
from unittest import mock

import pytest
from httpx import Headers, Response
from httpx import TimeoutException as HttpxTimeoutException

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model import HTTPRequest, HTTPTimeout
from blacksmith.service._async.adapters.httpx import AsyncHttpxTransport

headers = Headers()
headers["Content-Type"] = "application/json"

dummy_json = {"name": "Alice"}
dummy_error = {"detail": "error"}
dummy_response = Response(200, headers=headers, json=dummy_json)
dummy_empty_response = Response(204, headers=Headers(), json=None)
dummy_error_response = Response(422, headers=headers, json=dummy_error)
dummy_error_500_response = Response(500, headers=headers, text="internal server error")


def dummy_query_timeout():
    raise HttpxTimeoutException("ReadTimeout", request=None)  # type: ignore


@mock.patch(
    "httpx._client.AsyncClient.request",
    return_value=dummy_response,
)
async def test_query_http(patch: Any):
    transport = AsyncHttpxTransport()
    resp = await transport(HTTPRequest("GET", "/"), "cli", "/", HTTPTimeout())
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
async def test_query_http_204(patch: Any):
    transport = AsyncHttpxTransport()
    resp = await transport(HTTPRequest("GET", "/"), "cli", "/", HTTPTimeout())
    assert resp.status_code == 204
    assert dict(resp.headers) == {}
    assert resp.json == ""


@mock.patch(
    "httpx._client.AsyncClient.request",
    return_value=dummy_error_response,
)
async def test_query_http_422(patch: Any):
    transport = AsyncHttpxTransport()
    with pytest.raises(HTTPError) as ctx:
        await transport(HTTPRequest("POST", "/", body="{}"), "cli", "/", HTTPTimeout())

    assert str(ctx.value) == "cli - POST / - 422 Unprocessable Entity"
    assert ctx.value.status_code == 422
    assert ctx.value.json == dummy_error


@mock.patch(
    "httpx._client.AsyncClient.request",
    side_effect=lambda *args, **kwargs: dummy_query_timeout(),  # type: ignore
)
async def test_query_http_timeout(patch: Any):
    transport = AsyncHttpxTransport()
    with pytest.raises(TimeoutError) as ctx:
        await transport(HTTPRequest("DELETE", "/slow"), "cli", "/{xx}", HTTPTimeout())
    assert (
        str(ctx.value)
        == "cli - DELETE /{xx} - TimeoutException while calling DELETE /slow"
    )


@mock.patch(
    "httpx._client.AsyncClient.request",
    return_value=dummy_error_500_response,
)
async def test_query_http_no_json(patch: Any):
    transport = AsyncHttpxTransport()
    with pytest.raises(HTTPError) as ctx:
        await transport(HTTPRequest("POST", "/", body="{}"), "cli", "/", HTTPTimeout())

    assert str(ctx.value) == "cli - POST / - 500 Internal Server Error"
    assert ctx.value.status_code == 500
    assert ctx.value.json == {"error": "internal server error"}
