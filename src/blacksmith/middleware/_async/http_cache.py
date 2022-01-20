"""Collect metrics based on prometheus."""
import abc
from dataclasses import asdict
from datetime import timedelta
from typing import Optional, Type

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.model.middleware.http_cache import (
    AbstractCachePolicy,
    AbstractSerializer,
    CacheControlPolicy,
    JsonSerializer,
)
from blacksmith.typing import ClientName, Path

from .base import AsyncHTTPMiddleware, AsyncMiddleware


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


class AsyncHTTPCacheMiddleware(AsyncHTTPMiddleware):
    """
    Http Cache Middleware based on Cache-Control and redis.
    """

    def __init__(
        self,
        cache: AsyncAbstractCache,
        policy: AbstractCachePolicy = CacheControlPolicy(),
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
