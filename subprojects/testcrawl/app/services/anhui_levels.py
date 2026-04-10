"""
安徽自考 — 固定一级板块：
- 自考动态
- 考试安排
- 教材版本
- 主考院校
- 政策文件
- 助学管理
- 业务办理
- 本科
- 专科
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

ANHUI_ENTRY = "https://www.ahzsks.cn/gdjyzxks/"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("自考动态", "https://www.ahzsks.cn/gdjyzxks/search2.jsp?c=77"),
    ("考试安排", "https://www.ahzsks.cn/gdjyzxks/search2.jsp?c=80"),
    ("教材版本", "https://www.ahzsks.cn/gdjyzxks/search2.jsp?c=81"),
    ("主考院校", "https://www.ahzsks.cn/gdjyzxks/search2.jsp?c=79"),
    ("政策文件", "https://www.ahzsks.cn/gdjyzxks/search2.jsp?c=151"),
    ("助学管理", "https://www.ahzsks.cn/gdjyzxks/search2.jsp?c=152"),
    ("业务办理", "https://www.ahzsks.cn/gdjyzxks/search2.jsp?c=106"),
    ("本科", "https://www.ahzsks.cn/gdjyzxks/search2.jsp?c=109"),
    ("专科", "https://www.ahzsks.cn/gdjyzxks/search2.jsp?c=108"),
)


def get_anhui_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_anhui_list(soup, base_url=result.url)
        if not items:
            items = _stub_items(f"当前未解析到安徽自考「{display_name}」列表。")
        level1.append({"name": display_name, "items": items})
    return {"source_url": ANHUI_ENTRY, "level1": level1}


def _parse_anhui_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_anhui_content_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get("title") or a.get_text(" ", strip=True))
        if not title or title == "自考指南" or len(title) < 4:
            continue
        if full in seen:
            continue
        seen.add(full)
        li_text = ""
        li = a.find_parent("li")
        if li is not None:
            li_text = _clean_text(li.get_text(" ", strip=True))
        rows.append({"title": title, "url": full, "publish_date": _extract_date_like(li_text) or _extract_date_like(title)})
        if len(rows) >= max_items:
            break
    return rows


def _safe_anhui_content_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "ahzsks.cn" not in host:
        return None
    path = (p.path or "").lower()
    if "/gdjyzxks/" not in path:
        return None
    if "search2.jsp" in path:
        return None
    if not path.endswith((".htm", ".html")):
        return None
    return url


def _extract_date_like(text: str) -> str:
    m = re.search(r"(20\d{2})[-/](\d{2})[-/](\d{2})", text or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _stub_items(message: str) -> list[dict]:
    return [{"title": message, "url": ANHUI_ENTRY, "publish_date": ""}]

