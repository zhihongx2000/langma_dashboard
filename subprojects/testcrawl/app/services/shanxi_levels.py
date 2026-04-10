"""
山西省招生考试管理中心 — 自学考试（固定一级板块「自学考试」）。
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

SHANXI_ZXKS_ENTRY = "http://www.sxkszx.cn/news/zxks/index.html"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("自学考试", SHANXI_ZXKS_ENTRY),
)

_ARTICLE_PATH = re.compile(r"/news/\d+/n\d+\.html$", re.I)


def get_shanxi_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_shanxi_list(soup, base_url=result.url)
        if not items:
            items = _stub_items("当前未解析到山西自学考试列表。")
        level1.append({"name": display_name, "items": items})
    return {"source_url": SHANXI_ZXKS_ENTRY, "level1": level1}


def _parse_shanxi_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_shanxi_article_url(urljoin(base_url, href))
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
                "publish_date": _extract_date_like(li_text) or _extract_date_like(title),
            }
        )
        if len(rows) >= max_items:
            break
    return rows


def _safe_shanxi_article_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "sxkszx.cn" not in host:
        return None
    path = p.path or ""
    if not _ARTICLE_PATH.search(path.split("?")[0]):
        return None
    return url


def _extract_date_like(text: str) -> str:
    t = text or ""
    m = re.search(r"(20\d{2})年(\d{1,2})月(\d{1,2})日?", t)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m2 = re.search(r"(20\d{2})[-/.](\d{2})[-/.](\d{2})", t)
    if m2:
        return f"{m2.group(1)}-{m2.group(2)}-{m2.group(3)}"
    return ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _stub_items(message: str) -> list[dict]:
    return [{"title": message, "url": SHANXI_ZXKS_ENTRY, "publish_date": ""}]
