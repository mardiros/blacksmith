from blacksmith import AsyncClientFactory, AsyncPrometheusMetrics, AsyncConsulDiscovery
sd = AsyncConsulDiscovery()
cli = AsyncClientFactory(sd).add_middleware(AsyncPrometheusMetrics())
