import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

from app.scrapers.selectors import (
    ABOUT_DESCRIPTION_SELECTORS,
    ABOUT_WEBSITE_SELECTORS,
    INFO_ITEM_SELECTORS,
    LOGO_SELECTORS,
    NAME_SELECTORS,
    TAGLINE_SELECTORS,
)

FIXTURE_DIR = Path("tests/fixtures/linkedin")


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


def extract_summary(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    fields: dict = {}

    for sel in NAME_SELECTORS:
        element = soup.select_one(sel)
        if element:
            text = element.get_text(strip=True)
            if text:
                fields["name"] = text
                break

    for sel in TAGLINE_SELECTORS:
        element = soup.select_one(sel)
        if element:
            text = element.get_text(strip=True)
            if text:
                fields["tagline"] = text
                break

    for sel in LOGO_SELECTORS:
        element = soup.select_one(sel)
        if element:
            src = element.get("src")
            if src:
                fields["logo_url"] = src
                break

    for sel in INFO_ITEM_SELECTORS:
        elements = soup.select(sel)
        for el in elements:
            text = el.get_text(strip=True)
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


def extract_about(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    fields: dict = {}

    longest = ""
    for sel in ABOUT_DESCRIPTION_SELECTORS:
        elements = soup.select(sel)
        for el in elements:
            text = el.get_text(strip=True)
            if len(text) > len(longest):
                longest = text
    if longest:
        fields["description"] = longest

    for sel in ABOUT_WEBSITE_SELECTORS:
        for el in soup.select(sel):
            text = el.get_text(strip=True)
            if text and re.match(r"^https?://", text):
                fields["website"] = text
                break
        if "website" in fields:
            break
    for dt in soup.find_all("dt"):
        label = dt.get_text(strip=True).lower()
        dd = dt.find_next_sibling("dd")
        if dd is None:
            continue
        value = dd.get_text(strip=True)
        if not value:
            continue
        if "headquarters" in label:
            fields["headquarters"] = value
        elif "company size" in label or "size" in label:
            fields["company_size"] = value

    if "company_size" not in fields:
        for span in soup.find_all("span"):
            text = span.get_text(strip=True)
            if "associated members" in text.lower():
                fields["company_size"] = text
                break

    return fields


def main() -> None:
    page_id = sys.argv[1] if len(sys.argv) > 1 else "deepsolv"
    which = sys.argv[2] if len(sys.argv) > 2 else "summary"

    if which == "about":
        fixture = FIXTURE_DIR / f"{page_id}_about.html"
        extract_fn = extract_about
    else:
        fixture = FIXTURE_DIR / f"{page_id}.html"
        extract_fn = extract_summary

    if not fixture.exists():
        print(f"Fixture not found: {fixture}")
        sys.exit(1)

    html = fixture.read_text(encoding="utf-8")
    print(f"Loaded fixture: {fixture} ({len(html)} bytes)")

    fields = extract_fn(html)
    print("...extracted...")
    for key, value in fields.items():
        print(f"  {key}: {value!r}")
    if not fields:
        print(" (nothing extracted, selectors need adjustment)")


if __name__ == "__main__":
    main()
