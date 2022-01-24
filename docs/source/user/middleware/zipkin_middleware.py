from starlette_zipkin import trace

from blacksmith import (
    AbstractTraceContext,
    AsyncClientFactory,
    AsyncConsulDiscovery,
    AsyncZipkinMiddleware,
)

# AbstractTraceContext is an abtract base classe,
# register the class that already implement it.
AbstractTraceContext.register(trace)

sd = AsyncConsulDiscovery()
cli = AsyncClientFactory(sd)
cli.add_middleware(AsyncZipkinMiddleware(trace))
