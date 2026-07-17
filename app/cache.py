import json
from typing import Any
import redis.asyncio as redis
from app.core.logging import get_logger

logger=get_logger(__name__)

class Cache:
    def __init__(self, redis_url: str | None, ttl: int = 300):
        self._redis_url=redis_url
        self._client=redis.Redis | None
        self._ttl=ttl
        self._init_failed = False

    async def _get_client(self) -> redis.Redis | None:
        if self._client is not None:
            if isinstance(self._client, redis.Redis):
                return self._client
        if self._redis_url is None or self._init_failed:
            return None
        try:
            client = redis.from_url(self._redis_url, decode_responses=True)
            await client.ping()
            self._client = client
            logger.info("cache.connected", redis_url=self._redis_url)
        except Exception as exc:
            logger.warning("cache.init_failed", error=str(exc))
            self._init_failed = True
            return None
        return self._client

    async def get(self, key: str) -> Any | None:
        client = await self._get_client()
        if client is None:
            return None
        try:
            data = await client.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception as exc:
            logger.warning("cache.get_failed", key=key, error=str(exc))
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        client = await self._get_client()
        if client is None:
            return
        try:
            await client.set(key, json.dumps(value, default=str), ex=ttl or self._ttl)
        except Exception as exc:
            logger.warning("cache.set_failed", key=key, error=str(exc))


    async def delete(self, key: str) -> None:
        client = await self._get_client()
        if client is None:
            return
        try:
            await client.delete(key)
        except Exception as exc:
            logger.warning("cache.delete_failed", key=key, error=str(exc))
