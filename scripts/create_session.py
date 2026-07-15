
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

SESSION_PATH = Path("session.json")


async def main() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        await context.add_init_script(
            "() => { Object.defineProperty(navigator, 'webdriver', { get: () => false }); }"
        )
        page = await context.new_page()
        await page.goto("https://www.linkedin.com/login")
        print("A browser is open. Log in to linkedin manually.")
        print("When linkedin feed is open, come back here and press Enter...")
        input()

        await context.storage_state(path=str(SESSION_PATH))
        print(f"Session saved = {SESSION_PATH}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
