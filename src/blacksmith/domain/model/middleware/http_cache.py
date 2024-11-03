"""Collect metrics based on prometheus."""

import abc
import json
from typing import Any
from urllib.parse import urlencode

from httpx import Headers

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse
from blacksmith.typing import ClientName, Path


class AbstractCachePolicy(abc.ABC):
    """Define the Cache Policy"""

    @abc.abstractmethod
    def handle_request(
        self, req: HTTPRequest, client_name: ClientName, path: Path
    ) -> bool:
        """A function to decide if the http request is cachable."""

    @abc.abstractmethod
    def get_vary_key(
        self,
        client_name: ClientName,
        path: Path,
        request: HTTPRequest,
    ) -> str:
        """Create a caching key for the vary part."""

    @abc.abstractmethod
    def get_response_cache_key(
        self,
        client_name: ClientName,
        path: Path,
        req: HTTPRequest,
        vary: list[str],
    ) -> str:
        """Create a caching key for the http response."""

    @abc.abstractmethod
    def get_cache_info_for_response(
        self,
        client_name: ClientName,
        path: Path,
        req: HTTPRequest,
        resp: HTTPResponse,
    ) -> tuple[int, str, list[str]]:
        """Return caching info. Tuple (ttl in seconds, vary key, vary list)."""


class AbstractSerializer(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def loads(s: str) -> Any:
        """Load a string to an object"""

    @staticmethod
    @abc.abstractmethod
    def dumps(obj: Any) -> str:
        """Get a value from redis"""


class JsonSerializer(AbstractSerializer):
    @staticmethod
    def loads(s: str) -> Any:
        return json.loads(s)

    @staticmethod
    def dumps(obj: Any) -> str:
        return json.dumps(obj)


def int_or_0(val: str) -> int:
    try:
        ival = int(val)
    except ValueError:
        ival = 0
    return ival


def get_max_age(response: HTTPResponse) -> int:
    max_age = 0
    age = int_or_0(response.headers.get("age", "0"))
    s_cache_control = response.headers.get("cache-control", "")
    cache_control = [c.strip() for c in s_cache_control.split(",")]
    if "public" in cache_control:
        h_max_age: list[str] = [cc for cc in cache_control if cc.startswith("max-age=")]
        if h_max_age:
            _hdr, value = h_max_age[0].split("=", 1)
            max_age = int_or_0(value)
    return max(max_age - age, 0)


def get_vary_header_split(response: HTTPResponse) -> list[str]:
    vary = response.headers.get("vary", "")
    fields = [field.strip().lower() for field in vary.split(",")] if vary else []
    return fields


class CacheControlPolicy(AbstractCachePolicy):
    """
    Initialize the caching using `Cache-Control` http headers.
    Also consume the `Vary` response header to cache response per
    Vary response headers per request.

    :param sep: Separator used in cache key **MUST NOT BE USED** in client name.
    """

    def __init__(self, sep: str = "$") -> None:
        self.sep = sep

    def handle_request(
        self, req: HTTPRequest, client_name: ClientName, path: Path
    ) -> bool:
        return req.method == "GET"

    def get_vary_key(
        self, client_name: ClientName, path: Path, request: HTTPRequest
    ) -> str:
        path = path.format(**request.path)
        if request.querystring:
            qs = urlencode(request.querystring, doseq=True)
            path = f"{path}?{qs}"
        return f"{client_name}{self.sep}{path}"

    def get_response_cache_key(
        self,
        client_name: ClientName,
        path: Path,
        req: HTTPRequest,
        vary: list[str],
    ) -> str:
        headers = Headers(req.headers)
        vary_key = self.get_vary_key(client_name, path, req)
        vary_vals = [f"{key}={headers.get(key, '')}" for key in vary]
        response_cache_key = f"{vary_key}{self.sep}{'|'.join(vary_vals)}"
        return response_cache_key

    def get_cache_info_for_response(
        self,
        client_name: ClientName,
        path: Path,
        req: HTTPRequest,
        resp: HTTPResponse,
    ) -> tuple[int, str, list[str]]:
        max_age = get_max_age(resp)
        if max_age <= 0:
            return (max_age, "", [])
        vary_key = self.get_vary_key(client_name, path, req)
        vary = get_vary_header_split(resp)
        return (max_age, vary_key, vary)
