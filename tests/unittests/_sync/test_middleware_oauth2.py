from datetime import datetime, timezone

import pytest
from pydantic import SecretStr

from blacksmith import HTTPError
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.typing import SyncMiddleware
from blacksmith.middleware._sync.oauth2_token import (
    SyncOAuth2RefreshTokenMiddlewareFactory,
)
from blacksmith.service._sync.base import SyncAbstractTransport
from blacksmith.typing import ClientName, Path


class SyncDummyTransport(SyncAbstractTransport):
    def __init__(self, response: HTTPResponse):
        super().__init__()
        self.response = response

    def __call__(
        self,
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        """This is the next function of the middleware."""
        if self.response.status_code >= 400:
            raise HTTPError(
                f"{client_name} - {req.method} {path} - "
                f"{self.response.status_code} dummy error",
                req,
                self.response,
            )
        return self.response


def test_refresh_token(
    authenticated_bearer_middleware: SyncMiddleware,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):
    oauth2middleware = SyncOAuth2RefreshTokenMiddlewareFactory(
        client_id="client",
        client_secret=SecretStr("xxx-xx"),
        refresh_token=SecretStr("fresh"),
        token_url="https://example.net/token",
        transport=SyncDummyTransport(
            HTTPResponse(
                status_code=200,
                headers={},
                json={"access_token": "abc", "expires_in": 300},
            )
        ),
    )
    echo_next = oauth2middleware(authenticated_bearer_middleware)
    res = echo_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert oauth2middleware.access_token == SecretStr("abc")
    assert oauth2middleware.refresh_token == SecretStr("fresh")
    assert res.json == {"bandi_manchot": "777"}


def test_refresh_token_invalid(
    authenticated_bearer_middleware: SyncMiddleware,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):
    oauth2middleware = SyncOAuth2RefreshTokenMiddlewareFactory(
        client_id="client",
        client_secret=SecretStr("xxx-xx"),
        refresh_token=SecretStr("fresh"),
        token_url="https://example.net/token",
        transport=SyncDummyTransport(
            HTTPResponse(
                status_code=200,
                headers={},
                json={
                    "access_token": "pabon",
                    "refresh_token": "freshrenew",
                    "expires_in": 300,
                },
            )
        ),
    )
    echo_next = oauth2middleware(authenticated_bearer_middleware)
    res = echo_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert oauth2middleware.access_token == SecretStr("pabon")
    assert oauth2middleware.refresh_token == SecretStr("freshrenew")
    assert res.json == {"detail": "forbidden"}


def test_refresh_token_renew(
    authenticated_bearer_middleware: SyncMiddleware,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):
    oauth2middleware = SyncOAuth2RefreshTokenMiddlewareFactory(
        client_id="client",
        client_secret=SecretStr("xxx-xx"),
        refresh_token=SecretStr("fresh"),
        token_url="https://example.net/token",
        transport=SyncDummyTransport(
            HTTPResponse(
                status_code=200,
                headers={},
                json={
                    "access_token": "pabon",
                    "refresh_token": "freshrenew",
                    "expires_in": 300,
                },
            )
        ),
    )
    echo_next = oauth2middleware(authenticated_bearer_middleware)
    res = echo_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert res.json == {"detail": "forbidden"}
    oauth2middleware.expires_at = datetime.now(timezone.utc)
    assert oauth2middleware.bmclient
    oauth2middleware.bmclient.transport = SyncDummyTransport(
        HTTPResponse(
            status_code=200,
            headers={},
            json={
                "access_token": "abc",
                "refresh_token": "freshrenew",
                "expires_in": 300,
            },
        )
    )

    res = echo_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert res.json == {"bandi_manchot": "777"}


def test_no_token_given(
    authenticated_bearer_middleware: SyncMiddleware,
    dummy_http_request: HTTPRequest,
    dummy_timeout: HTTPTimeout,
):
    oauth2middleware = SyncOAuth2RefreshTokenMiddlewareFactory(
        client_id="client",
        client_secret=SecretStr("xxx-xx"),
        refresh_token=SecretStr("fresh"),
        token_url="https://example.net/token",
        transport=SyncDummyTransport(
            HTTPResponse(
                status_code=500,
                headers={},
                json={"detail": "oauth2 maintenance scheduled"},
            )
        ),
    )
    echo_next = oauth2middleware(authenticated_bearer_middleware)
    with pytest.raises(HTTPError) as ctx:
        echo_next(dummy_http_request, "dummy", "/dummies/{name}", dummy_timeout)
    assert ctx.value.response.json == {"detail": "oauth2 maintenance scheduled"}
