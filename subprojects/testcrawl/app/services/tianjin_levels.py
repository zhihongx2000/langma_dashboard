"""
天津招考资讯网 — 自学考试固定一级板块。
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

TJ_SOURCE_URL = "http://www.zhaokao.net/zxks/zyts/index.shtml"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("自学考试", "http://www.zhaokao.net/zxks/index.shtml"),
    ("自考考生服务平台", "http://www.zhaokao.net/sygl/system/2024/02/06/030006994.shtml"),
    ("重要提示", "http://www.zhaokao.net/zxks/zyts/index.shtml"),
    ("自考指南", "http://www.zhaokao.net/zxks/zkzn/index.shtml"),
    ("信息查询", "http://www.zhaokao.net/zxks/xxcx/index.shtml"),
    ("咨询渠道", "http://www.zhaokao.net/zxks/zxqd/index.shtml"),
)


def get_tianjin_levels() -> dict:
    payload: list[dict] = []
    for name, page_url in LEVEL1_SECTIONS:
        if name == "自考考生服务平台":
            payload.append(
                {
                    "name": name,
                    "items": [{"title": "自考考生服务平台", "url": page_url, "publish_date": ""}],
                }
            )
            continue
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_tj_list(soup, base_url=result.url)
        payload.append({"name": name, "items": items})
    return {"source_url": TJ_SOURCE_URL, "level1": payload}


def _parse_tj_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_tj_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get("title") or a.get_text(" ", strip=True))
        if len(title) < 4:
            continue
        if full in seen:
            continue
        seen.add(full)
        rows.append({"title": title, "url": full, "publish_date": _extract_date_like(title)})
        if len(rows) >= max_items:
            break
    return rows


def _safe_tj_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "zhaokao.net" not in host:
        return None
    path = (p.path or "").lower()
    if path.startswith("/zxks/system/") or path.startswith("/zxks/zkzn/") or path.startswith("/zxks/zxqd/"):
        return url
    if path.startswith("/zxks/xxcx/") or path.startswith("/zxks/zyts/") or path.startswith("/zxks/index"):
        return url
    return None


def _extract_date_like(text: str) -> str:
    m = re.search(r"(20\d{2})[-/](\d{2})[-/](\d{2})", text or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

