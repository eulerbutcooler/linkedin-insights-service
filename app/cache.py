import json
from typing import Any
import redis.asyncio as redis
from app.core.logging import get_logger

logger=get_logger(__name__)

class Cache:
    def __init__(self, client: redis.Redis | None, ttl: int = 300):
        self._client=client
        self._ttl=ttl

    async def get(self, key: str) -> Any | None:
        if self._client is None:
            return None
        try:
            data = await self._client.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception as exc:
            logger.warning("cache.get_failed", key=key, error=str(exc))
            return None

    async def set(self,key:str,value:Any,ttl:int | None = None) -> None:
        if self._client is None:
            return
        try:
            await self._client.set(key,json.dumps(value,default=str), ex=ttl or self._ttl)
        except Exception as exc:
            logger.warning("cache.set_failed", key=key, error=str(exc))

    async def delete(self, key: str)-> None:
        if self._client is None:
            return
        try:
            await self._client.delete(key)
        except Exception as exc:
            logger.warning("cache.delete_failed", key=key, error=str(exc))
