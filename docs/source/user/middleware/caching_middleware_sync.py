import redis

from blacksmith import SyncClientFactory, SyncConsulDiscovery, SyncHTTPCachingMiddleware

cache = redis.from_url("redis://redis/0")
sd = SyncConsulDiscovery()
cli = SyncClientFactory(sd).add_middleware(SyncHTTPCachingMiddleware(cache))
