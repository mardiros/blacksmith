import redis

from blacksmith import SyncClientFactory, SyncConsulDiscovery, SyncHTTPCacheMiddleware

cache = redis.from_url("redis://redis/0")
sd = SyncConsulDiscovery()
cli = SyncClientFactory(sd).add_middleware(SyncHTTPCacheMiddleware(cache))
cli.initialize()