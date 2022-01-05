import aioredis

from blacksmith import (
    AsyncClientFactory,
    AsyncHTTPCachingMiddleware,
    AsyncConsulDiscovery,
)

cache = aioredis.from_url("redis://redis/0")
sd = AsyncConsulDiscovery()
cli = AsyncClientFactory(sd).add_middleware(AsyncHTTPCachingMiddleware(cache))
