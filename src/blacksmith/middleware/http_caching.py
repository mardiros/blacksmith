"""Collect metrics based on prometheus."""
import abc
import json
from dataclasses import asdict
from datetime import timedelta
from typing import List, Optional, TYPE_CHECKING, Any, Callable
from urllib.parse import urlencode

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse
from blacksmith.domain.model.params import Request
from blacksmith.typing import ClientName, HttpMethod, Path

from .base import HTTPMiddleware, Middleware


class AbstractCache(abc.ABC):
    """Abstract Redis Client."""

    @abc.abstractmethod
    async def initialize(self):
        """Initialize the cache"""

    @abc.abstractmethod
    async def get(self, key: str) -> str:
        """Get a value from redis"""

    @abc.abstractmethod
    async def set(self, key: str, val: str, ex: timedelta):
        """Get a value from redis"""


try:
    from aioredis import Redis
    AbstractCache.register(Redis)
except ImportError:
    pass


def int_or_0(val: str) -> int:
    try:
        ival = int(val)
    except ValueError:
        ival = 0
    return ival


def get_max_age(response: HTTPResponse) -> int:
    max_age = 0
    age = int_or_0(response.headers.get("age", "0"))
    cache_control = response.headers.get("cache-control", "")
    cache_control = [c.strip() for c in cache_control.split(",")]
    if "public" in cache_control:
        h_max_age: List[str] = [cc for cc in cache_control if cc.startswith("max-age=")]
        if h_max_age:
            hdr, value = h_max_age[0].split("=", 1)
            max_age = int_or_0(value)
    return max(max_age - age, 0)


def get_vary_key(path: Path, request: HTTPRequest) -> str:
    path = path.format(**request.path)
    if request.querystring:
        qs = urlencode(request.querystring, doseq=True)
        path = f"{path}?{qs}"
    return path


def get_vary_header_split(response: HTTPResponse) -> List[str]:
    vary = response.headers.get("vary", "")
    fields = [field.strip().lower() for field in vary.split(",")] if vary else []
    return fields


class HttpCachingMiddleware(HTTPMiddleware):
    """
    Zipkin Middleware based on aiozipkin
    """

    def __init__(self, cache: AbstractCache) -> None:
        self._cache = cache

    def handle_request(
        self, req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
    ) -> bool:
        return method == "GET"

    async def cache_response(
        self,
        path: Path,
        req: HTTPRequest,
        resp: HTTPResponse,
    ):
        max_age = get_max_age(resp)
        if max_age <= 0:
            return
        ttl = timedelta(seconds=max_age)
        vary_key = get_vary_key(path, req)
        vary = get_vary_header_split(resp)
        vary_val = json.dumps(vary)
        await self._cache.set(vary_key, vary_val, ttl)
        vary_dict = {key: req.headers.get(key, "") for key in vary}
        resonse_cache_key = f"{vary_key}${json.dumps(vary_dict)}"
        response_cache = json.dumps(asdict(resp))
        await self._cache.set(resonse_cache_key, response_cache, ttl)

    async def get_from_cache(
        self, path: Path, req: HTTPRequest
    ) -> Optional[HTTPResponse]:
        vary_key = get_vary_key(path, req)
        vary_val = await self._cache.get(vary_key)
        if not vary_val:
            return None
        vary = json.loads(vary_val)
        vary_dict = {key: req.headers.get(key, "") for key in vary}
        resonse_cache_key = f"{vary_key}${json.dumps(vary_dict)}"
        val = await self._cache.get(resonse_cache_key)
        if not val:
            return None
        resp = json.loads(val)
        return HTTPResponse(**resp)


    def __call__(self, next: Middleware) -> Middleware:
        async def handle(
            req: HTTPRequest, method: HttpMethod, client_name: ClientName, path: Path
        ) -> HTTPResponse:

            if not self.handle_request(req, method, client_name, path):
                return await next(req, method, client_name, path)

            resp = await self.get_from_cache(path, req)
            if resp:
                return resp
            resp = await next(req, method, client_name, path)
            await self.cache_response(path, req, resp)
            return resp

        return handle
