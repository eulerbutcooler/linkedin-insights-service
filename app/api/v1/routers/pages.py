from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_page_service, get_cache
from app.cache import Cache
from app.services.page_service import PageService

router = APIRouter(prefix="/pages", tags=["pages"])


@router.get("")
async def list_pages(
    name: str | None = None,
    industry: str | None = None,
    followers_min: int | None = None,
    followers_max: int | None = None,
    cursor: str | None = None,
    size: int = Query(20, ge=1, le=50),
    service: PageService = Depends(get_page_service),
):
    pages, next_cursor = await service.list_pages(
        name=name,
        industry=industry,
        followers_min=followers_min,
        followers_max=followers_max,
        cursor=cursor,
        size=size,
    )
    return {
        "items": [p.model_dump(mode="json") for p in pages],
        "next_cursor": next_cursor,
    }


@router.get("/{linkedin_id}")
async def get_page(
    linkedin_id: str,
    service: PageService = Depends(get_page_service),
    cache: Cache = Depends(get_cache)
):
    cache_key=f"page:{linkedin_id}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached
    page = await service.get_or_fetch(linkedin_id)
    payload=page.model_dump(mode="json")
    await cache.set(cache_key, payload)
    return payload


@router.post("/{linkedin_id}/refresh")
async def refresh_page(
    linkedin_id: str,
    service: PageService = Depends(get_page_service),
    cache: Cache = Depends(get_cache)
):
    cache_key=f"page:{linkedin_id}"
    await cache.delete(cache_key)
    page = await service.refresh(linkedin_id)
    payload = page.model_dump(mode="json")
    await cache.set(cache_key,payload)
    return payload
