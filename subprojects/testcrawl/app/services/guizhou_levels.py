"""
贵州自考 — 固定一级板块：考试报名、专业计划、通知公告。
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

GUIZHOU_ENTRY = "http://zsksy.guizhou.gov.cn/zxks/ksjh/index.html"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("考试报名", "http://zsksy.guizhou.gov.cn/zxks/ksbm/"),
    ("专业计划", "http://zsksy.guizhou.gov.cn/zxks/ksjh/"),
    ("通知公告", "http://zsksy.guizhou.gov.cn/zxks/tzgg_5375724/"),
)

_ARTICLE_SUFFIX = re.compile(r"/t(20\d{6})_\d+\.html$", re.I)


def get_guizhou_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_guizhou_list(soup, base_url=result.url)
        if not items:
            items = _stub_items(f"当前未解析到贵州自考「{display_name}」列表。")
        level1.append({"name": display_name, "items": items})
    return {"source_url": GUIZHOU_ENTRY, "level1": level1}


def _parse_guizhou_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_guizhou_article_url(urljoin(base_url, href))
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
                "publish_date": _date_from_article_url(full) or _extract_date_like(li_text) or _extract_date_like(title),
            }
        )
        if len(rows) >= max_items:
            break
    return rows


def _safe_guizhou_article_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "zsksy.guizhou.gov.cn" not in host:
        return None
    path = (p.path or "").lower()
    if "/zxks/" not in path:
        return None
    if not path.endswith(".html"):
        return None
    if path.endswith("/index.html"):
        return None
    if not _ARTICLE_SUFFIX.search(path.split("?")[0]):
        return None
    return url


def _date_from_article_url(url: str) -> str:
    m = _ARTICLE_SUFFIX.search((urlparse(url).path or "").lower())
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
    return [{"title": message, "url": GUIZHOU_ENTRY, "publish_date": ""}]
