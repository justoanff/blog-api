import redis.asyncio as redis
from app.config.settings import get_settings

settings = get_settings()

redis_pool = redis.ConnectionPool.from_url(str(settings.REDIS_URL), decode_responses=True)

async def get_redis_client() -> redis.Redis:
    if not hasattr(get_redis_client, "client_instance") or get_redis_client.client_instance is None:
        print("Initializing Redis client")
        get_redis_client.client_instance = redis.Redis.from_url(str(settings.REDIS_URL), decode_responses = True)
    return get_redis_client.client_instance

async def close_redis_client():
    if hasattr(get_redis_client, "client_instance") and get_redis_client.client_instance:
        print("Closing Redis client")
        await get_redis_client.client_instance.close()
        get_redis_client.client_instance = None