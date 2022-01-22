from blacksmith import (
    AsyncCircuitBreakerMiddleware,
    AsyncClientFactory,
    AsyncConsulDiscovery,
)

sd = AsyncConsulDiscovery()
cli = AsyncClientFactory(sd).add_middleware(
    AsyncCircuitBreakerMiddleware(threshold=5, ttl=30)
)
