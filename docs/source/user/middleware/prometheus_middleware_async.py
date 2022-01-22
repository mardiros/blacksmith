from blacksmith import (
    AsyncClientFactory,
    AsyncConsulDiscovery,
    AsyncPrometheusMiddleware,
)

sd = AsyncConsulDiscovery()
cli = AsyncClientFactory(sd).add_middleware(AsyncPrometheusMiddleware())
