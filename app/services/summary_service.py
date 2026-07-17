import hashlib
import json

from app.cache import Cache
from app.db.page import PageDocument
from app.llm import LLMClient
from app.repositories.post import PostRepository


class SummaryService:
    def __init__(self, llm: LLMClient, post_repo: PostRepository, cache: Cache):
        self._llm = llm
        self._posts = post_repo
        self._cache = cache

    async def get_summary(self, page: PageDocument) -> dict:
        posts, _ = await self._posts.find_recent_for_page(page.linkedin_id, size=5)
        post_texts = [p.text for p in posts if p.text]
        content_inputs = {
            "name": page.name,
            "tagline": page.tagline,
            "industry": page.industry,
            "description": page.description,
            "followers": page.total_followers,
            "company_size": page.company_size,
            "headquarters": page.headquarters,
            "website": page.website,
            "recent_posts": post_texts,
        }
        content_hash = hashlib.sha256(
            json.dumps(content_inputs, sort_keys=True, default=str).encode()
        ).hexdigest()

        cache_key = f"summary:{page.linkedin_id}:{content_hash}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            cached["cached"]=True
            return cached

        system_prompt = (
            "You are a concise business analyst. Summarize a LinkedIn company "
            "page for a sales rep evaluating whether to reach out. Be specific, "
            "factual, and under 200 words. Do not invent facts not present in the input."
        )
        user_prompt = self._build_user_prompt(content_inputs)
        summary_text = await self._llm.summarize(system_prompt, user_prompt)

        payload = {
            "linkedin_id": page.linkedin_id,
            "summary": summary_text,
            "content_hash": content_hash,
            "cached": False,
        }
        await self._cache.set(cache_key, payload)
        return payload

    @staticmethod
    def _build_user_prompt(inputs: dict) -> str:
        posts_block = "\n\n".join(f"- {t[:200]}" for t in inputs["recent_posts"][:5])
        return f"""Company: {inputs['name']}
        Tagline: {inputs['tagline'] or 'N/A'}
        Industry: {inputs['industry'] or 'N/A'}
        Followers: {inputs['followers'] or 'N/A'}
        Size: {inputs['company_size'] or 'N/A'}
        HQ: {inputs['headquarters'] or 'N/A'}
        Website: {inputs['website'] or 'N/A'}
        Description:{inputs['description'] or 'N/A'}
        Recent posts (truncated):{posts_block or 'N/A'}
        Write a concise summary covering: what the company does, its positioning, and the vibe of its recent content."""
