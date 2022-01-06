from starlette_zipkin import trace

from blacksmith import (
    AbtractTraceContext,
    AsyncClientFactory,
    AsyncConsulDiscovery,
    AsyncZipkinMiddleware,
)

# AbtractTraceContext is an abtract base classe,
# register the class that already implement it.
AbtractTraceContext.register(trace)

sd = AsyncConsulDiscovery()
cli = AsyncClientFactory(sd)
cli.add_middleware(AsyncZipkinMiddleware(trace))
