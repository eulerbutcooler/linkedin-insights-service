from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.scrapers.dto import RawPage

class PageDocument(BaseModel):
    linkedin_id:str
    url:str

    name:str
    tagline: str | None = None
    industry: str | None = None
    total_followers: int | None = None
    logo_url: str | None = None
    description: str | None = None
    website: str | None = None
    headquarters: str | None = None
    company_size: str | None = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

def raw_page_to_document(raw:RawPage)->PageDocument:
    return PageDocument(
        linkedin_id=raw.linkedin_id,
        url=raw.url,
        name=raw.name or "Unknown",
        tagline=raw.tagline,
        industry=raw.industry,
        total_followers=raw.followers,
        logo_url=raw.logo_url,
        description=raw.description,
        website=raw.website,
        headquarters=raw.headquarters,
        company_size=raw.company_size,
    )
