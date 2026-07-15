import random
import re
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext

from app.scrapers.dto import RawPage
from app.scrapers.selectors import (
    ABOUT_DESCRIPTION_SELECTORS,
    ABOUT_WEBSITE_SELECTORS,
    INFO_ITEM_SELECTORS,
    LOGO_SELECTORS,
    NAME_SELECTORS,
    TAGLINE_SELECTORS,
)

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

AUTH_WALL_HINTS = ("authwall", "login", "signin", "/checkpoint/")


def _parse_count(text: str) -> int:
    if not text:
        return 0
    cleaned = text.replace(",", "")
    match = re.search(r"([\d.]+)\s*([KMB]?)", cleaned, re.IGNORECASE)
    if not match:
        return 0
    num = float(match.group(1))
    suffix = match.group(2).upper()
    if suffix == "K":
        num *= 1_000
    elif suffix == "M":
        num *= 1_000_000
    elif suffix == "B":
        num *= 1_000_000_000
    return int(num)


def _classify_info_item(text: str) -> str | None:
    lower = text.lower()
    if "follower" in lower:
        return "followers"
    if "employee" in lower:
        return "company_size"
    if re.search(r"\d+\s*[-–]\s*\d+", lower):
        return "company_size"
    if "k+" in lower or "m+" in lower:
        return "company_size"
    return "industry"


class LinkedinScraper:
    def __init__(self, browser: Browser, session_path: Path | None = None):
        self._browser = browser
        self._session_path = session_path

    async def _new_context(self) -> BrowserContext:
        kwargs: dict[str, Any] = {
            "user_agent": USER_AGENT,
            "viewport": {"width": 1280, "height": 900},
            "locale": "en-US",
        }
        if self._session_path and self._session_path.exists():
            kwargs["storage_state"] = str(self._session_path)
        context = await self._browser.new_context(**kwargs)
        await context.add_init_script(
            "() => { Object.defineProperty(navigator, 'webdriver', { get: () => false }); }"
        )
        return context

    async def fetch_page(self, page_id: str) -> RawPage:
        summary = await self._fetch_and_extract(page_id, subpath="", extractor="summary")

        try:
            about = await self._fetch_and_extract(page_id, subpath="about", extractor="about")
        except Exception:
            about = None

        if about is not None:
            for field in ("description", "website", "headquarters", "company_size", "specialties"):
                value = getattr(about, field, None)
                if value is not None and getattr(summary, field, None) is None:
                    setattr(summary, field, value)
        return summary

    async def _fetch_and_extract(self, page_id: str, subpath: str, extractor: str) -> RawPage:
        path = f"{page_id}/{subpath}" if subpath else page_id
        url = f"https://www.linkedin.com/company/{path}/"
        context = await self._new_context()
        try:
            page = await context.new_page()
            await self._simulate_mouse(page)

            response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            if response is None or response.status >= 400:
                raise RuntimeError(
                    f"Linkedin returned status {response.status if response else 'None'} for {url}"
                )
            final_url = page.url
            if any(hint in final_url.lower() for hint in AUTH_WALL_HINTS):
                raise RuntimeError(f"Auth wall hit while fetching {url}: redirected to {final_url}")

            await self._scroll(page)
            if extractor == "about":
                fields = await self._extract_about_fields(page)
            else:
                fields = await self._extract_summary_fields(page)

            return RawPage(
                linkedin_id=page_id,
                url=url,
                html=await page.content(),
                **fields,
            )
        finally:
            await context.close()


    async def _extract_summary_fields(self, page) -> dict:
        fields: dict[str, Any] = {}

        for sel in NAME_SELECTORS:
            element = await page.query_selector(sel)
            if element:
                text = (await element.text_content() or "").strip()
                if text:
                    fields["name"] = text
                    break

        for sel in TAGLINE_SELECTORS:
            element = await page.query_selector(sel)
            if element:
                text = (await element.text_content() or "").strip()
                if text:
                    fields["tagline"] = text
                    break

        for sel in LOGO_SELECTORS:
            element = await page.query_selector(sel)
            if element:
                src = await element.get_attribute("src")
                if src:
                    fields["logo_url"] = src
                    break

        for sel in INFO_ITEM_SELECTORS:
            elements = await page.query_selector_all(sel)
            for el in elements:
                text = (await el.text_content() or "").strip()
                if not text:
                    continue
                kind = _classify_info_item(text)
                if kind == "followers" and "followers" not in fields:
                    fields["followers"] = _parse_count(text)
                elif kind == "industry" and "industry" not in fields:
                    fields["industry"] = text
                elif kind == "company_size" and "company_size" not in fields:
                    fields["company_size"] = text
            if "followers" in fields and "industry" in fields:
                break

        return fields

    async def _extract_about_fields(self, page) -> dict:
        fields: dict[str, Any] = {}
        longest = ""
        for sel in ABOUT_DESCRIPTION_SELECTORS:
            elements = await page.query_selector_all(sel)
            for el in elements:
                text = (await el.text_content() or "").strip()
                if len(text) > len(longest):
                    longest = text
        if longest:
            fields["description"] = longest

        for sel in ABOUT_WEBSITE_SELECTORS:
            el = await page.query_selector_all(sel)
            for el in elements:
                text = (await el.text_content() or "").strip()
                if text and re.match(r"^https?://", text):
                    fields["website"] = text
                    break
            if "website" in fields:
                break
        dt_locator = page.locator("dt")
        count = await dt_locator.count()
        for i in range(count):
            dt = dt_locator.nth(i)
            label = (await dt.text_content() or "").strip().lower()
            dd = dt.locator("xpath=following-sibling::dd[1]")
            if await dd.count() == 0:
                continue
            value = (await dd.text_content() or "").strip()
            if not value:
                continue
            if "headquarters" in label:
                fields["headquarters"] = value
            elif "company size" in label or "size" in label:
                fields["company_size"] = value

        if "company_size" not in fields:
            spans = await page.query_selector_all("span")
            for span in spans:
                text = (await span.text_content() or "").strip()
                if "associated members" in text.lower():
                    fields["company_size"] = text
                    break

        return fields

    async def _simulate_mouse(self, page) -> None:
        for _ in range(3):
            await page.mouse.move(random.randint(100, 800), random.randint(100, 600))
            await page.wait_for_timeout(random.randint(50, 150))

    async def _scroll(self, page) -> None:
        for _ in range(4):
            await page.mouse.wheel(0, 800)
            await page.wait_for_timeout(random.randint(600, 1400))
