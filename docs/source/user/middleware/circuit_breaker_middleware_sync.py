from blacksmith import SyncClientFactory, SyncCircuitBreaker, SyncConsulDiscovery

sd = SyncConsulDiscovery()
cli = SyncClientFactory(sd).add_middleware(SyncCircuitBreaker(threshold=5, ttl=30))
