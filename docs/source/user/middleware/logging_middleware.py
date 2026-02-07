import logging

from blacksmith import (
    AsyncClientFactory,
    AsyncConsulDiscovery,
    AsyncLoggingMiddleware,
)


async def main():
    factory = AsyncClientFactory(AsyncConsulDiscovery())
    factory.add_middleware(AsyncLoggingMiddleware(logging.getLogger("my.http_traffic")))
