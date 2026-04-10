"""
山东省教育招生考试院 — 自学考试（固定一级板块）。
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

SHANDONG_ZXKS_ENTRY = "https://www.sdzk.cn/NewsListM.aspx?BCID=5&CID=1163"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("自学考试", SHANDONG_ZXKS_ENTRY),
)


def get_shandong_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_sd_list(soup, base_url=result.url)
        level1.append({"name": display_name, "items": items})
    return {"source_url": SHANDONG_ZXKS_ENTRY, "level1": level1}


def _parse_sd_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_sd_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get("title") or a.get_text(" ", strip=True))
        if len(title) < 4:
            continue
        if full in seen:
            continue
        seen.add(full)
        # 标题中常带日期，兜底从链接无日期时设空
        rows.append({"title": title, "url": full, "publish_date": _extract_date_like(title)})
        if len(rows) >= max_items:
            break
    return rows


def _safe_sd_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "sdzk.cn" not in host:
        return None
    path = (p.path or "").lower()
    if path.endswith("newsinfo.aspx"):
        return url
    return None


def _extract_date_like(text: str) -> str:
    m = re.search(r"(20\d{2})[-/](\d{2})[-/](\d{2})", text or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

