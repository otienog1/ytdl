import redis.asyncio as redis
from app.config.settings import settings
from app.utils.logger import logger


class RedisClient:
    _instance = None
    _client: redis.Redis = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
        return cls._instance

    async def connect(self):
        """Connect to Redis"""
        try:
            self._client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self._client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            raise

    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            logger.info("Redis connection closed")

    def get_client(self) -> redis.Redis:
        """Get Redis client"""
        return self._client


redis_client = RedisClient()
