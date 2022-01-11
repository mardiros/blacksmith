from purgatory import AsyncRedisUnitOfWork

from blacksmith import AsyncCircuitBreaker

breaker = AsyncCircuitBreaker(5, 30, uow=AsyncRedisUnitOfWork("redis://redis/0"))
