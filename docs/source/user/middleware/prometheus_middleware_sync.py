from blacksmith import SyncClientFactory, SyncConsulDiscovery, SyncPrometheusMiddleware

sd = SyncConsulDiscovery()
cli = SyncClientFactory(sd).add_middleware(SyncPrometheusMiddleware())
