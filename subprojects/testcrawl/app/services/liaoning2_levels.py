"""
辽宁（入口2）— 固定一级板块：
- 温馨提示
- 政策规定
- 考生须知
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

LIAONING2_ENTRY = "https://zk.lnzsks.com/lnzk.wb/"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("温馨提示", "https://zk.lnzsks.com/lnzk.wb/catalog/2"),
    ("政策规定", "https://zk.lnzsks.com/lnzk.wb/catalog/3"),
    ("考生须知", "https://zk.lnzsks.com/lnzk.wb/catalog/4"),
)


def get_liaoning2_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_liaoning2_list(soup, base_url=result.url)
        level1.append({"name": display_name, "items": items})
    return {"source_url": LIAONING2_ENTRY, "level1": level1}


def _parse_liaoning2_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_liaoning2_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get("title") or a.get_text(" ", strip=True))
        if len(title) < 4:
            continue
        if full in seen:
            continue
        seen.add(full)
        block_text = ""
        li = a.find_parent("li")
        if li is not None:
            block_text = _clean_text(li.get_text(" ", strip=True))
        rows.append(
            {
                "title": title,
                "url": full,
                "publish_date": _extract_date_like(block_text) or _extract_date_like(title),
            }
        )
        if len(rows) >= max_items:
            break
    return rows


def _safe_liaoning2_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "zk.lnzsks.com" not in host:
        return None
    path = (p.path or "").lower()
    if "/lnzk.wb/content/" not in path:
        return None
    return url


def _extract_date_like(text: str) -> str:
    m = re.search(r"(20\d{2})[-/](\d{2})[-/](\d{2})", text or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

