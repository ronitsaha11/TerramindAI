import redis.asyncio as redis

from src.core.config import settings


class RedisClient:
    def __init__(self) -> None:
        self.pool: redis.ConnectionPool | None = None
        self.client: redis.Redis | None = None

    async def connect(self) -> None:
        self.pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL, decode_responses=True
        )
        self.client = redis.Redis(connection_pool=self.pool)

    async def disconnect(self) -> None:
        if self.client:
            await self.client.aclose()
        if self.pool:
            await self.pool.disconnect()


redis_client = RedisClient()
