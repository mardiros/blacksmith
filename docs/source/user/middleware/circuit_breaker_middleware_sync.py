from blacksmith import SyncCircuitBreaker, SyncClientFactory, SyncConsulDiscovery

sd = SyncConsulDiscovery()
cli = SyncClientFactory(sd).add_middleware(SyncCircuitBreaker(threshold=5, ttl=30))
