"""
OAuth2.0 refresh token middleware.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import urlparse
from uuid import UUID

from pydantic import SecretStr

from blacksmith.domain.error import default_error_parser
from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model import ResponseBox
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.model.params import (
    CollectionParser,
    HeaderField,
    PostBodyField,
    Request,
    Response,
)
from blacksmith.domain.registry import ApiRoutes
from blacksmith.domain.typing import SyncMiddleware
from blacksmith.middleware._sync import SyncHTTPMiddleware
from blacksmith.service._sync.base import SyncAbstractTransport

if TYPE_CHECKING:
    from blacksmith.service._sync.client import SyncClient
from blacksmith.typing import ClientName, Path

log = logging.getLogger(__name__)


class GetToken(Request):
    content_type: str = HeaderField(
        "application/x-www-form-urlencoded", alias="Content-Type"
    )
    client_id: str | UUID = PostBodyField()
    client_secret: SecretStr = PostBodyField()
    grant_type: Literal["refresh_token"] = PostBodyField()
    refresh_token: SecretStr = PostBodyField()


class Token(Response):
    expires_in: int
    access_token: SecretStr
    refresh_token: SecretStr | None = None


class SyncOAuth2RefreshTokenMiddlewareFactory(SyncHTTPMiddleware):
    """
    A middleware based on OAuth2.0 using a refresh token.

    :param client_id: OAuth2.0 client id.
    :param client_secret: OAuth2.0 client secret.
    :param refresh_token: OAuth2.0 refresh token.
    :param oauth2authorization_server_origin: OAUth2 authorization server origin.
    :param oauth2authorization_token_pathinfo: OAUth2 authorization server path.
    :param transport: Blacksmith transport to use.
    :param timeout: HTTP timeout for the authorization server to retrieve token.
    :param middlewares: List of blacksmith middleware to the token http call.
    :param token_drift_seconds: Seconds to add to the expires in to avoid consuming
        an expired access token.
    """

    client_id: str | UUID
    client_secret: SecretStr | None
    refresh_token: SecretStr | None
    access_token: SecretStr | None
    expires_at: datetime | None

    def __init__(
        self,
        *,
        client_id: str | UUID,
        client_secret: SecretStr | None = None,
        refresh_token: SecretStr | None = None,
        token_url: str,
        transport: SyncAbstractTransport,
        timeout: HTTPTimeout | None = None,
        middlewares: list[SyncHTTPMiddleware] | None = None,
        token_drift_seconds: int = 30,
        raise_oauth2_error: bool = True,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
        self.expires_at = None
        self.token_drift_seconds = token_drift_seconds
        self.raise_oauth2_error = raise_oauth2_error

        self.token_url = token_url
        self.transport = transport
        self.timeout = timeout
        self.middlewares = middlewares
        self.bmclient: Any = None

    def get_client(self) -> "SyncClient[HTTPError]":
        if self.bmclient is None:
            from blacksmith import SyncClient  # avoid circular import

            assert self.token_url, "token url not initilized."
            token_url = urlparse(self.token_url)
            authz_server_url = f"{token_url.scheme}://{token_url.netloc}"

            self.bmclient = SyncClient(
                name="oauth2",
                endpoint=authz_server_url,
                resources={
                    "tokens": ApiRoutes(
                        path=token_url.path,
                        contract={"POST": (GetToken, Token)},
                        collection_path=None,
                        collection_contract=None,
                        collection_parser=None,
                    )
                },
                transport=self.transport,
                timeout=self.timeout or HTTPTimeout(),
                collection_parser=CollectionParser,
                middlewares=self.middlewares or [],
                error_parser=default_error_parser,
            )
        assert self.bmclient is not None
        return self.bmclient

    def get_new_token(self) -> None:
        assert self.client_secret is not None
        assert self.refresh_token is not None
        cli = self.get_client()
        rtoken: ResponseBox[Token, HTTPError] = cli.tokens.post(
            GetToken(
                client_id=self.client_id,
                client_secret=self.client_secret,
                grant_type="refresh_token",
                refresh_token=self.refresh_token,
            )
        )
        if rtoken.is_ok():
            token = rtoken.unwrap()
            self.expires_at = datetime.now(UTC) + timedelta(
                seconds=(token.expires_in - self.token_drift_seconds)
            )
            self.error = None
            self.access_token = token.access_token
            if token.refresh_token:
                self.refresh_token = token.refresh_token
        else:
            self.error = rtoken.unwrap_err()
            self.access_token = None

    def get_access_token(self) -> SecretStr | None:
        """Return an access token from the refresh_token"""
        if not self.expires_at or self.expires_at < datetime.now(UTC):
            self.get_new_token()
        return self.access_token

    def __call__(self, next: SyncMiddleware) -> SyncMiddleware:
        def handle(
            req: HTTPRequest,
            client_name: ClientName,
            path: Path,
            timeout: HTTPTimeout,
        ) -> HTTPResponse:
            token = self.get_access_token()
            if token:
                req.headers.update(
                    {"Authorization": f"Bearer {token.get_secret_value()}"}
                )
            else:
                log.error("No access token available")
                if self.raise_oauth2_error and self.error:
                    raise self.error
            return next(req, client_name, path, timeout)

        return handle
