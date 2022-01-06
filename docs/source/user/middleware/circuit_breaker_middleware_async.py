from blacksmith import AsyncClientFactory, AsyncCircuitBreaker, AsyncConsulDiscovery

sd = AsyncConsulDiscovery()
cli = AsyncClientFactory(sd).add_middleware(AsyncCircuitBreaker(threshold=5, ttl=30))
