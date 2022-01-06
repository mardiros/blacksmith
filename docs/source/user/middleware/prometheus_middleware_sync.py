from blacksmith import SyncClientFactory, SyncPrometheusMetrics, SyncConsulDiscovery
sd = SyncConsulDiscovery()
cli = SyncClientFactory(sd).add_middleware(SyncPrometheusMetrics())
