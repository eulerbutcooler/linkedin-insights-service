from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.scrapers.dto import RawComment, RawPost

class PostDocument(BaseModel):
    post_id: str
    urn: str | None = None
    linkedin_url: str
    page_id: str
    text: str | None = None
    posted_at: datetime | None = None
    likes: int | None = None
    comments_count: int | None = None
    shares: int | None = None
    author_name: str | None = None
    author_url: str | None = None
    author_avatar_url: str | None = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CommentDocument(BaseModel):
    comment_id: str
    post_id: str
    page_id: str
    text: str | None = None
    posted_at: datetime | None = None
    author_name: str | None = None
    author_url: str | None = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def raw_post_to_document(raw: RawPost, page_id: str) -> PostDocument:
    return PostDocument(
        post_id=raw.post_id,
        urn=None,
        linkedin_url=raw.linkedin_url,
        page_id=page_id,
        text=raw.text,
        posted_at=_parse_iso(raw.posted_at),
        likes=raw.likes,
        comments_count=raw.comments_count,
        shares=raw.shares,
        author_name=raw.author_name,
        author_url=raw.author_url,
        author_avatar_url=raw.author_avatar_url,
    )


def raw_comment_to_document(raw: RawComment, post_id: str, page_id: str) -> CommentDocument:
    return CommentDocument(
        comment_id=raw.comment_id,
        post_id=post_id,
        page_id=page_id,
        text=raw.text,
        posted_at=_parse_iso(raw.posted_at),
        author_name=raw.author_name,
        author_url=raw.author_url,
    )
