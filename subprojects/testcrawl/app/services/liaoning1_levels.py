"""
辽宁（入口1）— 自学考试（固定一级板块）。
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

LIAONING1_ZXKS_ENTRY = "https://www.lnzsks.com/listinfo/zxks_1.html"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("自学考试", LIAONING1_ZXKS_ENTRY),
)


def get_liaoning1_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_liaoning1_list(soup, base_url=result.url)
        level1.append({"name": display_name, "items": items})
    return {"source_url": LIAONING1_ZXKS_ENTRY, "level1": level1}


def _parse_liaoning1_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_liaoning1_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get("title") or a.get_text(" ", strip=True))
        if len(title) < 4:
            continue
        if full in seen:
            continue
        seen.add(full)
        li_text = ""
        li = a.find_parent("li")
        if li is not None:
            li_text = _clean_text(li.get_text(" ", strip=True))
        rows.append(
            {
                "title": title,
                "url": full,
                "publish_date": _extract_date_like(li_text) or _extract_date_like(title) or _extract_date_from_url(full),
            }
        )
        if len(rows) >= max_items:
            break
    return rows


def _safe_liaoning1_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "lnzsks.com" not in host:
        return None
    path = (p.path or "").lower()
    if "/newsinfo/" not in path or not path.endswith(".htm"):
        return None
    return url


def _extract_date_like(text: str) -> str:
    m = re.search(r"(20\d{2})[-/](\d{2})[-/](\d{2})", text or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def _extract_date_from_url(url: str) -> str:
    m = re.search(r"ims_(20\d{2})(\d{2})(\d{2})_", (url or "").lower())
    if not m:
        return ""
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

