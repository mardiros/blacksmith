"""Collect metrics based on prometheus."""
import abc
import json
from dataclasses import asdict
from datetime import timedelta
from typing import Any, List, Optional, Tuple, Type
from urllib.parse import urlencode

from httpx import Headers

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.typing import ClientName, Path

from .base import AsyncHTTPMiddleware, AsyncMiddleware


class AbstractCachingPolicy(abc.ABC):
    """Caching Policy"""

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
        vary: List[str],
    ) -> str:
        """Create a caching key for the http response."""

    @abc.abstractmethod
    def get_cache_info_for_response(
        self,
        client_name: ClientName,
        path: Path,
        req: HTTPRequest,
        resp: HTTPResponse,
    ) -> Tuple[int, str, List[str]]:
        """Return caching info. Tuple (ttl in seconds, vary key, vary list)."""


class AsyncAbstractCache(abc.ABC):
    """Abstract Redis Client."""

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the cache"""

    @abc.abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get a value from redis"""

    @abc.abstractmethod
    async def set(self, key: str, val: str, ex: timedelta) -> None:
        """Get a value from redis"""


try:
    from aioredis import Redis

    AsyncAbstractCache.register(Redis)
except ImportError:
    pass


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
        h_max_age: List[str] = [cc for cc in cache_control if cc.startswith("max-age=")]
        if h_max_age:
            _hdr, value = h_max_age[0].split("=", 1)
            max_age = int_or_0(value)
    return max(max_age - age, 0)


def get_vary_header_split(response: HTTPResponse) -> List[str]:
    vary = response.headers.get("vary", "")
    fields = [field.strip().lower() for field in vary.split(",")] if vary else []
    return fields


class CacheControlPolicy(AbstractCachingPolicy):
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
        vary: List[str],
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
    ) -> Tuple[int, str, List[str]]:
        max_age = get_max_age(resp)
        if max_age <= 0:
            return (max_age, "", [])
        vary_key = self.get_vary_key(client_name, path, req)
        vary = get_vary_header_split(resp)
        return (max_age, vary_key, vary)


class AsyncHTTPCachingMiddleware(AsyncHTTPMiddleware):
    """
    Http Cache Middleware based on Cache-Control and redis.
    """

    def __init__(
        self,
        cache: AsyncAbstractCache,
        policy: AbstractCachingPolicy = CacheControlPolicy(),
        serializer: Type[AbstractSerializer] = JsonSerializer,
    ) -> None:
        self._cache = cache
        self._policy = policy
        self._serializer = serializer

    async def initialize(self) -> None:
        try:
            await self._cache.initialize()
        except AttributeError:  # coverage-ignore
            # the redis sync version does not implement this method
            pass

    async def cache_response(
        self,
        client_name: ClientName,
        path: Path,
        req: HTTPRequest,
        resp: HTTPResponse,
    ) -> None:
        (
            ttl,
            vary_key,
            vary,
        ) = self._policy.get_cache_info_for_response(client_name, path, req, resp)
        if ttl <= 0:
            return
        ttld = timedelta(seconds=ttl)
        vary_val = self._serializer.dumps(vary)
        await self._cache.set(vary_key, vary_val, ttld)

        response_cache_key = self._policy.get_response_cache_key(
            client_name, path, req, vary
        )
        resp.headers = dict(resp.headers)
        response_cache = self._serializer.dumps(asdict(resp))
        await self._cache.set(response_cache_key, response_cache, ttld)

    async def get_from_cache(
        self, client_name: ClientName, path: Path, req: HTTPRequest
    ) -> Optional[HTTPResponse]:
        vary_key = self._policy.get_vary_key(client_name, path, req)
        vary_val = await self._cache.get(vary_key)
        if not vary_val:
            return None
        vary = self._serializer.loads(vary_val)
        response_cache_key = self._policy.get_response_cache_key(
            client_name, path, req, vary
        )
        val = await self._cache.get(response_cache_key)
        if not val:
            return None
        resp = self._serializer.loads(val)
        return HTTPResponse(**resp)

    def __call__(self, next: AsyncMiddleware) -> AsyncMiddleware:
        async def handle(
            req: HTTPRequest,
            client_name: ClientName,
            path: Path,
            timeout: HTTPTimeout,
        ) -> HTTPResponse:

            if not self._policy.handle_request(req, client_name, path):
                return await next(req, client_name, path, timeout)

            resp = await self.get_from_cache(client_name, path, req)
            if resp:
                return resp
            resp = await next(req, client_name, path, timeout)
            await self.cache_response(client_name, path, req, resp)
            return resp

        return handle
