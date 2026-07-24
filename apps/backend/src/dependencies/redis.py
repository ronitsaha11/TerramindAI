from collections.abc import AsyncGenerator

from redis.asyncio import Redis

from src.core.redis import redis_client


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    Dependency for getting an async redis client.
    """
    if redis_client.client is None:
        raise RuntimeError("Redis client is not initialized")

    # We yield the same client instance since redis.asyncio handles multiplexing
    yield redis_client.client
