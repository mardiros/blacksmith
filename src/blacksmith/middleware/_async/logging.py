"""
Logging the traffic using python logging.
"""

import logging
import time
from urllib.parse import urlencode, urlparse

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.typing import ClientName, Path

from .base import AsyncHTTPMiddleware, AsyncMiddleware


class AsyncLoggingMiddleware(AsyncHTTPMiddleware):
    """
    Logging Middleware based on an python logging.

    :param logger: the logger to use. By default the logger of the current module
        will be used.
    :param log_response: force to log or not to log the http response body.
        logging the reponse body on a production server is discouraged here
        since it may reveal secrets since the logging happens before the pydantic
        validation. The default value is based on the logger level DEBUG.
        The error are logged with error level "ERROR" but requires the log_response
        to be true.
    """

    def __init__(
        self, logger: logging.Logger | None = None, log_response: bool | None = None
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.log_response = (
            self.logger.isEnabledFor(logging.DEBUG)
            if log_response is None
            else log_response
        )

    def log(
        self,
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        status_code: int | None,
        error: Exception | None,
        latency: float,
    ) -> None:
        req_url = urlparse(req.url)
        origin = f"{req_url.scheme}://{req_url.netloc}"
        fpath = path.format(**req.path)
        if req.querystring:
            fpath = f"{fpath}?{urlencode(req.querystring, doseq=True)}"

        self.logger.info(
            "%s %s - %s %s - %s %.3fs",
            client_name,
            origin,
            req.method,
            fpath,
            str(status_code),
            latency,
        )
        if error is not None:
            self.logger.error(str(error))
            if isinstance(error, HTTPError) and self.log_response:
                self.logger.error(error.response.json)

    def __call__(self, next: AsyncMiddleware) -> AsyncMiddleware:
        async def handle(
            req: HTTPRequest,
            client_name: ClientName,
            path: Path,
            timeout: HTTPTimeout,
        ) -> HTTPResponse:
            start = time.perf_counter()
            try:
                resp = await next(req, client_name, path, timeout)
            except HTTPError as exc:
                latency = time.perf_counter() - start
                status_code = exc.response.status_code
                self.log(req, client_name, path, status_code, exc, latency)
                raise
            except Exception as exc:
                latency = time.perf_counter() - start
                status_code = None
                self.log(req, client_name, path, status_code, exc, latency)
                raise
            else:
                latency = time.perf_counter() - start
                status_code = resp.status_code
                self.log(req, client_name, path, status_code, None, latency)
                if self.log_response:
                    self.logger.debug(resp.json)
                return resp

        return handle
