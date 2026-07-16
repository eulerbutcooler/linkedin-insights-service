from fastapi import APIRouter, Depends, Query
from app.api.v1.deps import get_person_repo
from app.repositories.post import PersonRepository

router = APIRouter(tags=["people"])

@router.get("/pages/{linkedin_id}/people")
async def list_people(
    linkedin_id: str,
    cursor: str | None = None,
    size: int = Query(25, ge=1, le=50),
    person_repo: PersonRepository = Depends(get_person_repo),
):
    people, next_cursor = await person_repo.find_for_page(
        linkedin_id, cursor=cursor, size=size
    )
    return {
        "items": [p.model_dump(mode="json") for p in people],
        "next_cursor": next_cursor,
    }
