from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.deps import get_page_repo, get_summary_service
from app.core.exceptions import NotFoundError
from app.repositories.page import PageRepository
from app.services.summary_service import SummaryService

router = APIRouter(tags=["summary"])


@router.get("/pages/{linkedin_id}/summary")
async def get_summary(
    linkedin_id: str,
    page_repo: PageRepository = Depends(get_page_repo),
    summary_service: SummaryService | None = Depends(get_summary_service),
):
    page = await page_repo.find_by_linkedin_id(linkedin_id)
    if page is None:
        raise NotFoundError(f"Page {linkedin_id} not found. Fetch it first via GET /pages/{linkedin_id}")
    if summary_service is None:
        raise HTTPException(status_code=501, detail="LLM summary not configured (set GEMINI_API_KEY)")
    return await summary_service.get_summary(page)
