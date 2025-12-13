"""Collect metrics based on prometheus."""

import abc
import time
from dataclasses import asdict
from datetime import timedelta
from typing import Literal

from blacksmith.domain.model.http import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.model.middleware.http_cache import (
    AbstractCachePolicy,
    AbstractSerializer,
    CacheControlPolicy,
    JsonSerializer,
)
from blacksmith.domain.model.middleware.prometheus import PrometheusMetrics
from blacksmith.typing import ClientName, HTTPMethod, Path

from .base import AsyncHTTPMiddleware, AsyncMiddleware

CachableState = Literal["uncachable_request", "uncachable_response", "cached"]
default_cache_control = CacheControlPolicy()


class AsyncAbstractCache(abc.ABC):
    """Abstract Redis Client."""

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the cache"""

    @abc.abstractmethod
    async def get(self, key: str) -> str | None:
        """Get a value from redis"""

    @abc.abstractmethod
    async def set(self, key: str, val: str, ex: timedelta) -> None:
        """Get a value from redis"""


try:
    from redis.asyncio import Redis

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
        metrics: PrometheusMetrics | None = None,
        policy: AbstractCachePolicy = default_cache_control,
        serializer: type[AbstractSerializer] = JsonSerializer,
    ) -> None:
        self._cache = cache
        self._policy = policy
        self._serializer = serializer
        self._metrics = metrics

    async def initialize(self) -> None:
        try:
            await self._cache.initialize()
        except AttributeError:  # coverage: ignore
            # the redis sync version does not implement this method
            ...

    async def cache_response(
        self,
        client_name: ClientName,
        path: Path,
        req: HTTPRequest,
        resp: HTTPResponse,
    ) -> bool:
        (
            ttl,
            vary_key,
            vary,
        ) = self._policy.get_cache_info_for_response(client_name, path, req, resp)
        if ttl <= 0:
            return False
        ttld = timedelta(seconds=ttl)
        vary_val = self._serializer.dumps(vary)
        await self._cache.set(vary_key, vary_val, ttld)

        response_cache_key = self._policy.get_response_cache_key(
            client_name, path, req, vary
        )
        resp.headers = dict(resp.headers)
        response_cache = self._serializer.dumps(asdict(resp))
        await self._cache.set(response_cache_key, response_cache, ttld)
        return True

    async def get_from_cache(
        self, client_name: ClientName, path: Path, req: HTTPRequest
    ) -> HTTPResponse | None:
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
            start = time.perf_counter()
            if not self._policy.handle_request(req, client_name, path):
                resp = await next(req, client_name, path, timeout)
                self.inc_cache_miss(
                    client_name,
                    "uncachable_request",
                    req.method,
                    path,
                    resp.status_code,
                )
                return resp

            resp_from_cache = await self.get_from_cache(client_name, path, req)
            if resp_from_cache:
                latency = time.perf_counter() - start
                self.observe_cache_hit(
                    client_name, req.method, path, resp_from_cache.status_code, latency
                )
                return resp_from_cache

            resp = await next(req, client_name, path, timeout)
            is_cached = await self.cache_response(client_name, path, req, resp)
            state: CachableState = "cached" if is_cached else "uncachable_response"
            self.inc_cache_miss(client_name, state, req.method, path, resp.status_code)
            return resp

        return handle

    def observe_cache_hit(
        self, client_name: str, method: str, path: str, status_code: int, latency: float
    ) -> None:
        if self._metrics:
            self._metrics.blacksmith_cache_hit.labels(
                client_name=client_name,
                method=method,
                path=path,
                status_code=status_code,
            ).inc()
            self._metrics.blacksmith_cache_latency_seconds.labels(
                client_name=client_name,
                method=method,
                path=path,
                status_code=status_code,
            ).observe(latency)

    def inc_cache_miss(
        self,
        client_name: str,
        cachable_state: CachableState,
        method: HTTPMethod,
        path: str,
        status_code: int,
    ) -> None:
        if self._metrics:
            self._metrics.blacksmith_cache_miss.labels(
                client_name=client_name,
                cachable_state=cachable_state,
                method=method,
                path=path,
                status_code=status_code,
            ).inc()
