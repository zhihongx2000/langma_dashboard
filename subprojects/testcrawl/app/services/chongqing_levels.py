"""
重庆市教育考试院 — 固定一级板块：自学考试。
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

CHONGQING_ZXKS_ENTRY = "https://www.cqksy.cn/web/column/col1846543.html"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("自学考试", CHONGQING_ZXKS_ENTRY),
)


def get_chongqing_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_chongqing_list(soup, base_url=result.url)
        if not items:
            items = _stub_items(f"当前未解析到重庆自考「{display_name}」列表，可先从官网栏目页手动进入查看。")
        level1.append({"name": display_name, "items": items})
    return {"source_url": CHONGQING_ZXKS_ENTRY, "level1": level1}


def _parse_chongqing_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_chongqing_article_url(urljoin(base_url, href))
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
                "publish_date": _extract_date_like(li_text) or _extract_date_like(title) or _date_from_article_url(full),
            }
        )
        if len(rows) >= max_items:
            break
    return rows


def _safe_chongqing_article_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "cqksy.cn" not in host:
        return None
    path = (p.path or "").lower()
    # 官方常见正文路径：/web/article/...
    if "/web/article/" in path and path.endswith(".html"):
        return url
    return None


def _date_from_article_url(url: str) -> str:
    m = re.search(r"/(20\d{2})(\d{2})(\d{2})/", url or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def _extract_date_like(text: str) -> str:
    m = re.search(r"(20\d{2})[-/](\d{2})[-/](\d{2})", text or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _stub_items(message: str) -> list[dict]:
    return [{"title": message, "url": CHONGQING_ZXKS_ENTRY, "publish_date": ""}]

