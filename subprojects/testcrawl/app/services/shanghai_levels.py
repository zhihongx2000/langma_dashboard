"""
上海市教育考试院（上海招考热线）— 自学考试固定一级板块：
自考新闻、考试日程、政策法规、大纲教材。
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

SHANGHAI_ENTRY = "https://www.shmeea.edu.cn/page/04000/"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("自考新闻", "https://www.shmeea.edu.cn/page/04100/"),
    ("考试日程", "https://www.shmeea.edu.cn/page/04200/"),
    ("政策法规", "https://www.shmeea.edu.cn/page/04300/"),
    ("大纲教材", "https://www.shmeea.edu.cn/page/04400/"),
)

_ARTICLE_PATH = re.compile(r"/page/04\d{3}/\d{8}/\d+\.html?$", re.I)


def get_shanghai_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_shanghai_list(soup, base_url=result.url)
        if not items:
            items = _stub_items(f"当前未解析到上海自考「{display_name}」列表。")
        level1.append({"name": display_name, "items": items})
    return {"source_url": SHANGHAI_ENTRY, "level1": level1}


def _parse_shanghai_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_shanghai_article_url(urljoin(base_url, href))
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


def _safe_shanghai_article_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "shmeea.edu.cn" not in host:
        return None
    path = (p.path or "").split("?")[0].lower()
    if not _ARTICLE_PATH.search(path):
        return None
    return url


def _extract_date_like(text: str) -> str:
    m = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", text or "")
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _stub_items(message: str) -> list[dict]:
    return [{"title": message, "url": SHANGHAI_ENTRY, "publish_date": ""}]
