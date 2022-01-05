import aioredis

from blacksmith import (
    SyncClientFactory,
    SyncHTTPCachingMiddleware,
    SyncConsulDiscovery,
)

cache = aioredis.from_url("redis://redis/0")
sd = SyncConsulDiscovery()
cli = SyncClientFactory(sd).add_middleware(SyncHTTPCachingMiddleware(cache))
