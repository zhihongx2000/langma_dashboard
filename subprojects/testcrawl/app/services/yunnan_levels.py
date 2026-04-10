"""
云南省招考频道 — 自学考试（固定一级板块）。

入口：`https://www.ynzs.cn/html/web/zkdt-zxks/index.html`
解析规则：
- 一级固定仅「自学考试」
- 详情页收录 `https://www.ynzs.cn/html/content/*.html`
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

YUNNAN_ZXKS_ENTRY = "https://www.ynzs.cn/html/web/zkdt-zxks/index.html"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("自学考试", YUNNAN_ZXKS_ENTRY),
)


def get_yunnan_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_yunnan_list(soup, base_url=result.url)
        level1.append({"name": display_name, "items": items})
    return {"source_url": YUNNAN_ZXKS_ENTRY, "level1": level1}


def _parse_yunnan_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_yunnan_content_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get_text(" ", strip=True))
        if len(title) < 4:
            continue
        if full in seen:
            continue
        seen.add(full)
        rows.append({"title": title, "url": full, "publish_date": _extract_date_like(title)})
        if len(rows) >= max_items:
            break
    return rows


def _safe_yunnan_content_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "ynzs.cn" not in host:
        return None
    path = (p.path or "").lower()
    if not re.search(r"^/html/content/\d+\.html$", path):
        return None
    return url


def _extract_date_like(text: str) -> str:
    m = re.search(r"(20\d{2})[/-](\d{1,2})[/-](\d{1,2})", text)
    if not m:
        return ""
    y = m.group(1)
    mm = m.group(2).zfill(2)
    dd = m.group(3).zfill(2)
    return f"{y}-{mm}-{dd}"


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

