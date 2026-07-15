import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

from app.scrapers.scraper import LinkedinScraper

FIXTURE_DIR = Path("tests/fixtures/linkedin")


async def main(page_id: str) -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],)
        scraper = LinkedinScraper(browser, session_path=Path("session.json"))
        try:
            raw_summary = await scraper.fetch_page(page_id)
            summary_fixture = FIXTURE_DIR / f"{page_id}.html"
            summary_fixture.write_text(raw_summary.html, encoding="utf-8")
            print(f"summary fixture -> {summary_fixture} ({len(raw_summary.html)} bytes)")

            raw_about = await scraper.fetch_page(page_id, subpath="about")
            about_fixture = FIXTURE_DIR / f"{page_id}_about.html"
            about_fixture.write_text(raw_about.html, encoding="utf-8")
            print(f"about fixture    -> {about_fixture} ({len(raw_about.html)} bytes)")

            print("\n--- fields extracted from summary page ---")
            print(f"  name:      {raw_summary.name!r}")
            print(f"  tagline:   {raw_summary.tagline!r}")
            print(f"  industry:  {raw_summary.industry!r}")
            print(f"  followers: {raw_summary.followers}")
            print(f"  logo_url:  {raw_summary.logo_url!r}")
        except Exception as exc:
            print(f"FAILED: {exc}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "deepsolv"))
