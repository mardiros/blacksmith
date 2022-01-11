from blacksmith import SyncClientFactory, SyncConsulDiscovery, SyncPrometheusMetrics

sd = SyncConsulDiscovery()
cli = SyncClientFactory(sd).add_middleware(SyncPrometheusMetrics())
