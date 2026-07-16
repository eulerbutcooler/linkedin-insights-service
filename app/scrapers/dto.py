from dataclasses import dataclass

@dataclass
class RawPage:
    linkedin_id:str
    url:str
    name: str | None = None
    followers: int | None = None
    tagline: str | None = None
    industry: str | None = None
    logo_url: str | None = None
    description: str | None = None
    website: str | None = None
    headquarters: str | None = None
    company_size: str | None = None
    scraped_at: str | None = None

@dataclass
class RawPost:
    post_id: str
    linkedin_url: str
    text: str | None = None
    posted_at: str | None = None
    likes: int | None = None
    comments_count: int | None = None
    shares: int | None = None
    author_name: str | None = None
    author_url: str | None = None
    author_avatar_url: str | None = None

@dataclass
class RawComment:
    comment_id: str
    text: str | None = None
    posted_at: str | None = None
    author_name: str | None = None
    author_url: str | None = None
    likes: int | None = None

@dataclass
class RawPerson:
    person_id: str
    name: str | None = None
    title: str | None = None
    profile_url: str | None = None
    profile_pic_url: str | None = None
    location: str | None = None
    followers: int | None = None
