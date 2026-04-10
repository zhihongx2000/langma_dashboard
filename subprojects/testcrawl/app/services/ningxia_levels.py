"""
宁夏教育考试院 — 高等教育自学考试（固定一级板块）。

入口：`https://www.nxjyks.cn/contents/ZXKS/`
解析规则：
- 一级固定仅「高等教育自学考试」
- 仅收录 `/contents/ZXKS/YYYY/MM/*.html` 详情页
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

NINGXIA_ZXKS_ENTRY = "https://www.nxjyks.cn/contents/ZXKS/"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("高等教育自学考试", NINGXIA_ZXKS_ENTRY),
)


def get_ningxia_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_ningxia_list(soup, base_url=result.url)
        level1.append({"name": display_name, "items": items})
    return {"source_url": NINGXIA_ZXKS_ENTRY, "level1": level1}


def _parse_ningxia_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 100) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_ningxia_zxks_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get_text(" ", strip=True))
        if len(title) < 4:
            continue
        if full in seen:
            continue
        seen.add(full)
        rows.append({"title": title, "url": full, "publish_date": _extract_date_from_url(full)})
        if len(rows) >= max_items:
            break
    return rows


def _safe_ningxia_zxks_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "nxjyks.cn" not in host:
        return None
    path = (p.path or "")
    if not re.search(r"^/contents/ZXKS/\d{4}/\d{2}/\d+\.html$", path):
        return None
    return url


def _extract_date_from_url(url: str) -> str:
    m = re.search(r"/contents/ZXKS/(?P<y>20\d{2})/(?P<m>\d{2})/", url)
    if not m:
        return ""
    return f"{m.group('y')}-{m.group('m')}-01"


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

