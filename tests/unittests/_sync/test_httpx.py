from typing import Any
from unittest import mock

import pytest
from httpx import Headers, Response
from httpx import TimeoutException as HttpxTimeoutException

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model import HTTPRequest, HTTPTimeout
from blacksmith.service._sync.adapters.httpx import SyncHttpxTransport, build_headers

headers = Headers()
headers["Content-Type"] = "application/json"

dummy_json = {"name": "Alice"}
dummy_error = {"detail": "error"}
dummy_response = Response(200, headers=headers, json=dummy_json)
dummy_empty_response = Response(204, headers=Headers(), json=None)
dummy_error_response = Response(422, headers=headers, json=dummy_error)
dummy_error_500_response = Response(500, headers=headers, text="internal server error")


def dummy_query_timeout() -> None:
    raise HttpxTimeoutException("ReadTimeout", request=None)  # type: ignore


@mock.patch(
    "httpx._client.Client.request",
    return_value=dummy_response,
)
def test_query_http(patch: Any) -> None:
    transport = SyncHttpxTransport()
    resp = transport(
        HTTPRequest(method="GET", url_pattern="/"), "cli", "/", HTTPTimeout()
    )
    assert resp.status_code == 200
    assert dict(resp.headers) == {
        "content-length": "17",
        "content-type": "application/json",
    }
    assert resp.json == dummy_json


def test_build_headers_default() -> None:
    req = HTTPRequest(method="GET", url_pattern="/", headers={}, body="{}")
    assert build_headers(req) == {"Content-Type": "application/json"}


def test_build_headers_no_body() -> None:
    req = HTTPRequest(method="GET", url_pattern="/", headers={}, body="")
    assert build_headers(req) == {}


def test_build_headers_copy() -> None:
    req = HTTPRequest(method="GET", url_pattern="/", headers={"A": "a"}, body="")
    copy = build_headers(req)
    assert copy is not req.headers


def test_build_headers() -> None:
    req = HTTPRequest(
        method="GET",
        url_pattern="/",
        headers={"Content-Type": "application/json+magic"},
        body="{}",
    )
    assert build_headers(req) == {"Content-Type": "application/json+magic"}


@mock.patch(
    "httpx._client.Client.request",
    return_value=dummy_empty_response,
)
def test_query_http_204(patch: Any) -> None:
    transport = SyncHttpxTransport()
    resp = transport(
        HTTPRequest(method="GET", url_pattern="/"), "cli", "/", HTTPTimeout()
    )
    assert resp.status_code == 204
    assert dict(resp.headers) == {}
    assert resp.json == ""


@mock.patch(
    "httpx._client.Client.request",
    return_value=dummy_error_response,
)
def test_query_http_422(patch: Any) -> None:
    transport = SyncHttpxTransport()
    with pytest.raises(HTTPError) as ctx:
        transport(
            HTTPRequest(method="POST", url_pattern="/", body="{}"),
            "cli",
            "/",
            HTTPTimeout(),
        )

    assert str(ctx.value) == "cli - POST / - 422 Unprocessable Entity"
    assert ctx.value.status_code == 422
    assert ctx.value.json == dummy_error


@mock.patch(
    "httpx._client.Client.request",
    side_effect=lambda *args, **kwargs: dummy_query_timeout(),  # type: ignore
)
def test_query_http_timeout(patch: Any) -> None:
    transport = SyncHttpxTransport()
    with pytest.raises(TimeoutError) as ctx:
        transport(
            HTTPRequest(method="DELETE", url_pattern="/slow"),
            "cli",
            "/{xx}",
            HTTPTimeout(),
        )
    assert (
        str(ctx.value)
        == "cli - DELETE /{xx} - TimeoutException while calling DELETE /slow"
    )


@mock.patch(
    "httpx._client.Client.request",
    return_value=dummy_error_500_response,
)
def test_query_http_not_json(patch: Any) -> None:
    transport = SyncHttpxTransport()
    with pytest.raises(HTTPError) as ctx:
        transport(
            HTTPRequest(method="POST", url_pattern="/", body="{}"),
            "cli",
            "/",
            HTTPTimeout(),
        )

    assert str(ctx.value) == "cli - POST / - 500 Internal Server Error"
    assert ctx.value.status_code == 500
    assert ctx.value.json == {"error": "internal server error"}
