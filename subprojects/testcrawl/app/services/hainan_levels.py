"""
海南省考试局 — 自学考试（固定一级板块）。

入口页：`http://ea.hainan.gov.cn/ywdt/zxks/`
解析策略：
- 一级固定仅「自学考试」
- 列表项仅保留 `.../ywdt/zxks/...` 文章链接
- 日期优先从 URL 中 `tYYYYMMDD_` 片段提取
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

HAINAN_ZXKS_ENTRY = "http://ea.hainan.gov.cn/ywdt/zxks/"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("自学考试", HAINAN_ZXKS_ENTRY),
)


def get_hainan_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_zxks_links(soup, base_url=result.url)
        level1.append({"name": display_name, "items": items})

    return {"source_url": HAINAN_ZXKS_ENTRY, "level1": level1}


def _parse_zxks_links(soup: BeautifulSoup, *, base_url: str, max_items: int = 100) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_hainan_zxks_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get_text(" ", strip=True))
        title = re.sub(r"^【[^】]{1,8}】\s*", "", title)
        if len(title) < 4:
            continue
        if full in seen:
            continue
        seen.add(full)
        rows.append(
            {
                "title": title,
                "url": full,
                "publish_date": _extract_date_from_url(full),
            }
        )
        if len(rows) >= max_items:
            break
    return rows


def _safe_hainan_zxks_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "ea.hainan.gov.cn" not in host:
        return None
    path = (p.path or "").lower()
    if "/ywdt/zxks/" not in path:
        return None
    if not path.endswith(".html"):
        return None
    return url


def _extract_date_from_url(url: str) -> str:
    m = re.search(r"/t(?P<y>20\d{2})(?P<m>\d{2})(?P<d>\d{2})_", url)
    if not m:
        return ""
    return f"{m.group('y')}-{m.group('m')}-{m.group('d')}"


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

