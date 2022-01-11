from blacksmith import AsyncClientFactory, AsyncConsulDiscovery, AsyncPrometheusMetrics

sd = AsyncConsulDiscovery()
cli = AsyncClientFactory(sd).add_middleware(AsyncPrometheusMetrics())
