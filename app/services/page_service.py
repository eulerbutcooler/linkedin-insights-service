import re
from app.core.exceptions import ScrapeError
from app.db.page import raw_page_to_document
from app.db.post import raw_comment_to_document, raw_post_to_document
from app.repositories.page import PageRepository
from app.repositories.post import CommentRepository, PostRepository
from app.scrapers.apify_client import ApifyClient
from app.db.person import raw_person_to_document
from app.repositories.post import PersonRepository



class PageService:
    def __init__(
        self,
        page_repo: PageRepository,
        post_repo: PostRepository,
        comment_repo: CommentRepository,
        person_repo: PersonRepository,
        apify: ApifyClient,
    ):
        self._pages = page_repo
        self._posts = post_repo
        self._comments = comment_repo
        self._people = person_repo
        self._apify = apify

    async def get_or_fetch(self, linkedin_id: str):
        page = await self._pages.find_by_linkedin_id(linkedin_id)
        if page:
            return page
        return await self._scrape_and_store(linkedin_id)

    async def refresh(self, linkedin_id: str):
        return await self._scrape_and_store(linkedin_id)

    async def list_pages(
        self,
        name: str | None = None,
        industry: str | None = None,
        followers_min: int | None = None,
        followers_max: int | None = None,
        cursor: str | None = None,
        size: int = 20,
    ):
        filter_doc: dict = {}
        if name:
            filter_doc["$text"] = {"$search": name}
        if industry:
            filter_doc["industry"] = {"$regex": re.escape(industry), "$options": "i"}

        fol: dict = {}
        if followers_min is not None:
            fol["$gte"] = followers_min
        if followers_max is not None:
            fol["$lte"] = followers_max
        if fol:
            filter_doc["total_followers"] = fol
        return await self._pages.find_many(filter_doc, cursor=cursor, size=size)

    async def _scrape_and_store(self, linkedin_id: str):
        try:
            raw_page = await self._apify.fetch_company(linkedin_id)
        except Exception as exc:
            raise ScrapeError(f"Failed to scrape company {linkedin_id}: {exc}") from exc

        page_doc = raw_page_to_document(raw_page)
        stored = await self._pages.upsert(page_doc)

        try:
            posts = await self._apify.fetch_posts(linkedin_id)
        except Exception:
            return stored

        for raw_post, raw_comments in posts:
            post_doc = raw_post_to_document(raw_post, page_id=linkedin_id)
            await self._posts.upsert(post_doc)
            for raw_comment in raw_comments:
                comment_doc = raw_comment_to_document(
                    raw_comment,
                    post_id=raw_post.post_id,
                    page_id=linkedin_id,
                )
                await self._comments.upsert(comment_doc)
        try:
            employees = await self._apify.fetch_employees(linkedin_id)
        except Exception:
            return stored
        for raw_person in employees:
            person_doc = raw_person_to_document(raw_person, page_id=linkedin_id)
            await self._people.upsert(person_doc)
        return stored
