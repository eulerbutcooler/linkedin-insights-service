from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.scrapers.dto import RawPerson


class PersonDocument(BaseModel):
    person_id: str
    page_id: str
    name: str | None = None
    title: str | None = None
    profile_url: str | None = None
    profile_pic_url: str | None = None
    location: str | None = None
    followers: int | None = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def raw_person_to_document(raw: RawPerson, page_id: str) -> PersonDocument:
    return PersonDocument(
        person_id=raw.person_id,
        page_id=page_id,
        name=raw.name,
        title=raw.title,
        profile_url=raw.profile_url,
        profile_pic_url=raw.profile_pic_url,
        location=raw.location,
        followers=raw.followers,
    )
