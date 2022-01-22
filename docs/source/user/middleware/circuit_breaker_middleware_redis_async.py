from purgatory import AsyncRedisUnitOfWork

from blacksmith import AsyncCircuitBreakerMiddleware

breaker = AsyncCircuitBreakerMiddleware(
    5, 30, uow=AsyncRedisUnitOfWork("redis://redis/0")
)
