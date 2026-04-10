"""
广西招生考试院 — 自学考试：固定一级「通知公告」「招生问答」「招考日程」。

招生问答列表对应官网栏目路径 kswd.htm（导航常为「考试问答」，与用户所称招生问答为同一列表页）。
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

GUANGXI_ENTRY = "https://www.gxeea.cn/zxks/tzgg.htm"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("通知公告", "https://www.gxeea.cn/zxks/tzgg.htm"),
    ("招生问答", "https://www.gxeea.cn/zxks/kswd.htm"),
    ("招考日程", "https://www.gxeea.cn/zxks/zkrc.htm"),
)

_CONTENT_ARTICLE = re.compile(r"/view/content_\d+_\d+\.html?$", re.I)


def get_guangxi_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_guangxi_list(soup, base_url=result.url)
        if not items:
            items = _stub_items(f"当前未解析到广西自学考试「{display_name}」列表。")
        level1.append({"name": display_name, "items": items})
    return {"source_url": GUANGXI_ENTRY, "level1": level1}


def _parse_guangxi_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_guangxi_article_url(urljoin(base_url, href))
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


def _safe_guangxi_article_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "gxeea.cn" not in host:
        return None
    path = (p.path or "").split("?")[0].lower()
    if "/view/" not in path:
        return None
    if not _CONTENT_ARTICLE.search(path):
        return None
    return url


def _extract_date_like(text: str) -> str:
    m = re.search(r"(20\d{2})年(\d{1,2})月(\d{1,2})日?", text or "")
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m2 = re.search(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", text or "")
    if m2:
        return f"{m2.group(1)}-{int(m2.group(2)):02d}-{int(m2.group(3)):02d}"
    return ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _stub_items(message: str) -> list[dict]:
    return [{"title": message, "url": GUANGXI_ENTRY, "publish_date": ""}]
