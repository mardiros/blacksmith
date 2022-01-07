from purgatory import SyncRedisUnitOfWork
from blacksmith import SyncCircuitBreaker

breaker = SyncCircuitBreaker(5, 30, uow=SyncRedisUnitOfWork("redis://redis/0"))
