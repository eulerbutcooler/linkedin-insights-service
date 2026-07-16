from typing import Any
import httpx

from app.scrapers.dto import RawComment, RawPage, RawPost, RawPerson

APIFY_BASE="https://api.apify.com/v2"
COMPANY_ACTOR_ID = "harvestapi~linkedin-company"
POSTS_ACTOR_ID = "harvestapi~linkedin-profile-posts"
EMPLOYEES_ACTOR_ID = "harvestapi~linkedin-company-employees"

class ApifyClient:
    def __init__(self, api_token: str, timeout: float = 120.0):
        if not api_token:
            raise ValueError("apify_api_token is required")
        self._token=api_token
        self._timeout=timeout

    async def _run_actor_sync(self, actor_id: str, run_input: dict[str, Any])->list[dict[str,Any]]:
        url=f"{APIFY_BASE}/acts/{actor_id}/run-sync-get-dataset-items"
        params={"token": self._token}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp=await client.post(url, params=params, json=run_input)
            resp.raise_for_status()
            data=resp.json()
        if not isinstance(data,list):
            raise RuntimeError(f"Apify returned non-list response: {type(data).__name__}")
        return data

    async def fetch_company(self,linkedin_id:str)->RawPage:
        company_url = f"https://www.linkedin.com/company/{linkedin_id}/"
        run_input = {"companies": [company_url]}
        items = await self._run_actor_sync(COMPANY_ACTOR_ID, run_input)
        if not items:
            raise RuntimeError(f"Apify returned no items for company '{linkedin_id}'")
        return self._map_company(items[0], linkedin_id)

    @staticmethod
    def _map_company(item: dict[str, Any], fallback_id: str) -> RawPage:
        """Map Apify's company JSON to our RawPage DTO."""
        locations = item.get("locations") or []
        hq = next((loc for loc in locations if loc.get("headquarter")), None)
        if hq:
            parsed = hq.get("parsed") or {}
            headquarters = parsed.get("text") or hq.get("description")
        else:
            headquarters = None
        industries = item.get("industries") or []
        if industries:
            first=industries[0]
            if isinstance(first,dict):
                industry=first.get("name") or first.get("title")
            else:
                industry=first
        else:
            industry=None
        emp_count = item.get("employeeCount")
        emp_range = item.get("employeeCountRange") or {}
        if emp_count is not None:
            company_size = f"{emp_count} employees"
        elif emp_range.get("start"):
            company_size = f"{emp_range['start']}+ employees"
        else:
            company_size = None
        return RawPage(
            linkedin_id=item.get("universalName") or fallback_id,
            url=item.get("linkedinUrl") or f"https://www.linkedin.com/company/{fallback_id}/",
            name=item.get("name") or "Unknown",
            tagline=item.get("tagline"),
            description=item.get("description"),
            website=item.get("website"),
            logo_url=item.get("logo"),
            industry=industry,
            followers=item.get("followerCount"),
            company_size=company_size,
            headquarters=headquarters,
            scraped_at=item.get("updatedAt"),)

    async def fetch_posts(
        self, linkedin_id: str, max_posts: int = 15,
        max_comments_per_post: int = 5,
    ) -> list[tuple[RawPost, list[RawComment]]]:

        company_url=f"https://www.linkedin.com/company/{linkedin_id}/"
        run_input: dict[str, Any] = {
            "targetUrls": [company_url],
            "maxPosts": max_posts,
            "scrapeComments": max_comments_per_post > 0,
            "maxComments": max_comments_per_post,
            "scrapeReactions": False,
            "maxReactions": 0,
            "includeQuotePosts": False,
            "includeReposts": True,
            "postNestedComments": False,
            "postNestedReactions": False,
        }
        items = await self._run_actor_sync(POSTS_ACTOR_ID, run_input)

        posts: list[dict[str,Any]]=[]
        comments_by_post: dict[str,list[dict[str,Any]]]={}
        for item in items:
            if item.get("type")=="post":
                posts.append(item)
            elif item.get("type")=="comment":
                parent_id=item.get("postId")
                if parent_id:
                    comments_by_post.setdefault(parent_id, []).append(item)

        result: list[tuple[RawPost, list[RawComment]]] = []
        for post_item in posts:
            post_id = str(post_item.get("id") or "")
            post_comments = [
                self._map_comment(c)
                for c in comments_by_post.get(post_id, [])
            ]
            result.append((self._map_post(post_item), post_comments))
        return result
    @staticmethod
    def _map_post(item: dict[str, Any]) -> RawPost:
        author = item.get("author") or {}
        posted_at_obj = item.get("postedAt") or {}
        engagement = item.get("engagement") or {}
        return RawPost(
            post_id=str(item.get("id") or ""),
            linkedin_url=item.get("linkedinUrl") or "",
            text=item.get("content"),
            posted_at=posted_at_obj.get("date"),
            likes=engagement.get("likes"),
            comments_count=engagement.get("comments"),
            shares=engagement.get("shares"),
            author_name=author.get("name"),
            author_url=author.get("linkedinUrl"),
            author_avatar_url=(author.get("avatar") or {}).get("url")
        )

    @staticmethod
    def _map_comment(item: dict[str, Any])->RawComment:
        actor = item.get("actor") or {}
        engagement = item.get("engagement") or {}
        return RawComment(
            comment_id=str(item.get("id") or ""),
            text=item.get("commentary"),
            posted_at=item.get("createdAt"),
            author_name=actor.get("name"),
            author_url=actor.get("linkedinUrl"),
            likes=engagement.get("likes"),
        )

    async def fetch_employees(
        self,
        linkedin_id: str,
        max_employees: int = 25,
    ) -> list[RawPerson]:
        company_url = f"https://www.linkedin.com/company/{linkedin_id}/"
        run_input: dict[str, Any] = {
            "companies": [company_url],
            "maxItems": max_employees,
            "recentlyChangedJobs": False,
        }
        items = await self._run_actor_sync(EMPLOYEES_ACTOR_ID, run_input)
        return [self._map_person(item) for item in items]

    @staticmethod
    def _map_person(item: dict[str, Any]) -> RawPerson:
        location = item.get("location") or {}
        if isinstance(location, dict):
            location_text = location.get("linkedinText") or (location.get("parsed") or {}).get("text")
        else:
            location_text = location

        name = None
        first = item.get("firstName")
        last = item.get("lastName")
        if first or last:
            name = f"{first or ''} {last or ''}".strip()

        return RawPerson(
            person_id=str(item.get("id") or item.get("publicIdentifier") or ""),
            name=name or item.get("fullName"),
            title=item.get("headline"),
            profile_url=item.get("linkedinUrl"),
            profile_pic_url=None,
            location=location_text,
            followers=item.get("followerCount"),
        )
