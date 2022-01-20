import aioredis

from blacksmith import (
    AsyncClientFactory,
    AsyncConsulDiscovery,
    AsyncHTTPCacheMiddleware,
)

cache = aioredis.from_url("redis://redis/0")
sd = AsyncConsulDiscovery()
cli = AsyncClientFactory(sd).add_middleware(AsyncHTTPCacheMiddleware(cache))
