import asyncio

import aioredis

from blacksmith import (
    AsyncClientFactory,
    AsyncConsulDiscovery,
    AsyncHTTPCacheMiddleware,
)


async def main():
    cache = aioredis.from_url("redis://redis/0")
    sd = AsyncConsulDiscovery()
    cli = AsyncClientFactory(sd).add_middleware(AsyncHTTPCacheMiddleware(cache))
    await cli.initialize()


asyncio.run(main())
