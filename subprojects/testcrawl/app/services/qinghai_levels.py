"""
青海省教育考试网 — 自学考试（固定一级板块）。

入口页：`https://www.qhjyks.com/zyym/ztzl/zxksz/index.htm`
解析策略：
- 一级固定仅「自学考试」
- 列表区 ``ul.Culr-list01 > li``：``span.date`` 为发布日期，``a`` 为标题与链接
- 仅保留 `/zyym/ztzl/zxksz/` 下的详情页链接（`.htm/.html`）；无该列表结构时退回全页链接扫描（日期为空）
- 过滤分页 `index*.htm` 与纯数字标题
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

QINGHAI_ZXKS_ENTRY = "https://www.qhjyks.com/zyym/ztzl/zxksz/index.htm"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("自学考试", QINGHAI_ZXKS_ENTRY),
)


def get_qinghai_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_qinghai_list(soup, base_url=result.url)
        level1.append({"name": display_name, "items": items})
    return {"source_url": QINGHAI_ZXKS_ENTRY, "level1": level1}


def _parse_qinghai_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 100) -> list[dict]:
    """
    官网列表为 ``ul.Culr-list01``，每项 ``<li><span class="date">YYYY-MM-DD</span><a href="....htm">标题</a>``。
    """
    rows: list[dict] = []
    seen: set[str] = set()

    for li in soup.select("ul.Culr-list01 > li"):
        a = li.find("a", href=True)
        if not a:
            continue
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_qinghai_zxks_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get_text(" ", strip=True))
        if len(title) < 4:
            continue
        if re.fullmatch(r"\d+", title):
            continue
        date_el = li.select_one("span.date")
        publish_date = _clean_text(date_el.get_text(" ", strip=True) if date_el else "")
        if full in seen:
            continue
        seen.add(full)
        rows.append({"title": title, "url": full, "publish_date": publish_date})
        if len(rows) >= max_items:
            return rows

    if rows:
        return rows

    # 旧版页面或结构变化：退回全页链接扫描（无日期）
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_qinghai_zxks_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get_text(" ", strip=True))
        if len(title) < 4:
            continue
        if re.fullmatch(r"\d+", title):
            continue
        if full in seen:
            continue
        seen.add(full)
        rows.append({"title": title, "url": full, "publish_date": ""})
        if len(rows) >= max_items:
            break
    return rows


def _safe_qinghai_zxks_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "qhjyks.com" not in host:
        return None
    path = (p.path or "").lower()
    if "/zyym/ztzl/zxksz/" not in path:
        return None
    if not path.endswith((".htm", ".html")):
        return None
    if re.search(r"/index\d*\.htm[l]?$", path):
        return None
    return url


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

