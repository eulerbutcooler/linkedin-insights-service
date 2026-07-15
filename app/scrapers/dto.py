from dataclasses import dataclass

@dataclass
class RawPage:
    linkedin_id:str
    url:str
    html:str
    name: str | None = None
    followers: int | None = None
    tagline: str | None = None
    industry: str | None = None
    logo_url: str | None = None
    description: str | None = None
    website: str | None = None
    headquarters: str | None = None
    company_size: str | None = None
