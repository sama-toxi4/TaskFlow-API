import json
from typing import Optional, Any

import redis.asyncio as redis

from app.core.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


async def get_cache(key: str) -> Optional[Any]:
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None


async def set_cache(key: str, value, ttl: int = 1000000) -> None:
    await redis_client.set(key, json.dumps(value, default=str), ex=ttl)


async def delete_cache(key:str) -> None:
    await redis_client.delete(key)