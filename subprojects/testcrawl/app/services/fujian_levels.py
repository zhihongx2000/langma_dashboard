"""
福建自考 — 固定一级板块：公示公告、自考动态、政策文件。
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

FUJIAN_ENTRY = "https://www.eeafj.cn/zxks/"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("公示公告", "https://www.eeafj.cn/zkgsgg/"),
    ("自考动态", "https://www.eeafj.cn/zkzkdt/"),
    ("政策文件", "https://www.eeafj.cn/zkzkzc/"),
)

_SLUGS = ("zkgsgg", "zkzkdt", "zkzkzc")
_DATE_IN_PATH = re.compile(r"/(\d{8})/\d+\.html$", re.I)


def get_fujian_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_fujian_list(soup, base_url=result.url)
        if not items:
            items = _stub_items(f"当前未解析到福建自考「{display_name}」列表。")
        level1.append({"name": display_name, "items": items})
    return {"source_url": FUJIAN_ENTRY, "level1": level1}


def _parse_fujian_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_fujian_article_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get("title") or a.get_text(" ", strip=True))
        title = re.sub(r"^\[\d{1,2}-\d{1,2}\]\s*", "", title).strip()
        if len(title) < 4:
            continue
        if full in seen:
            continue
        seen.add(full)
        rows.append(
            {
                "title": title,
                "url": full,
                "publish_date": _date_from_article_url(full) or _extract_date_like(title),
            }
        )
        if len(rows) >= max_items:
            break
    return rows


def _safe_fujian_article_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "eeafj.cn" not in host:
        return None
    path = (p.path or "").lower()
    if not path.endswith(".html"):
        return None
    if not any(f"/{s}/" in path for s in _SLUGS):
        return None
    if not _DATE_IN_PATH.search(path):
        return None
    return url


def _date_from_article_url(url: str) -> str:
    m = _DATE_IN_PATH.search((urlparse(url).path or "").lower())
    if not m:
        return ""
    d = m.group(1)
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}"


def _extract_date_like(text: str) -> str:
    m = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", text or "")
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _stub_items(message: str) -> list[dict]:
    return [{"title": message, "url": FUJIAN_ENTRY, "publish_date": ""}]
