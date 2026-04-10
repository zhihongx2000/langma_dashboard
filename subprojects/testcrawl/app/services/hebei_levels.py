"""
河北省教育考试院自考系统 — 固定一级板块：
- 最新通知公告
- 查询中心
- 考生必读
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

HEBEI_ENTRY = "http://zk.hebeea.edu.cn/HebzkWeb/index"

LEVEL1_SECTIONS: tuple[str, ...] = ("最新通知公告", "查询中心", "考生必读")


def get_hebei_levels() -> dict:
    result = fetch_html(HEBEI_ENTRY, timeout_sec=30, prefer_browser=True)
    soup = BeautifulSoup(result.html, "lxml")
    notice = _parse_notice_block(soup)
    query = _parse_query_block(soup)
    must_read = _parse_must_read_block(soup)
    return {
        "source_url": result.url,
        "level1": [
            {"name": "最新通知公告", "items": notice},
            {"name": "查询中心", "items": query},
            {"name": "考生必读", "items": must_read},
        ],
    }


def _parse_notice_block(soup: BeautifulSoup, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for box in soup.select("div.tongzhi_list_box"):
        a = box.select_one("div.tongzhi_nr a[href]")
        if not a:
            continue
        href = (a.get("href") or "").strip()
        full = _safe_hebei_url(urljoin(HEBEI_ENTRY, href))
        if not full or full in seen:
            continue
        seen.add(full)
        title = _clean_text(a.get("title") or a.get_text(" ", strip=True))
        date_el = box.select_one("div.tongzhi_fabushijian")
        publish_date = _normalize_date(_clean_text(date_el.get_text(" ", strip=True) if date_el else ""))
        rows.append({"title": title, "url": full, "publish_date": publish_date})
        if len(rows) >= max_items:
            break
    return rows


def _parse_query_block(soup: BeautifulSoup, max_items: int = 80) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    # 查询中心块中都是 li > a
    for a in soup.select("div.chaxun ul li a[href]"):
        href = (a.get("href") or "").strip()
        full = _safe_hebei_url(urljoin(HEBEI_ENTRY, href))
        if not full or full in seen:
            continue
        seen.add(full)
        title = _clean_text(a.get_text(" ", strip=True))
        if len(title) < 2:
            continue
        rows.append({"title": title, "url": full, "publish_date": ""})
        if len(rows) >= max_items:
            break
    return rows


def _parse_must_read_block(soup: BeautifulSoup, max_items: int = 80) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    # 考生必读块：标题区域后紧跟若干 li
    for a in soup.select("div.bidu ul li a[href], div.ksbd ul li a[href], div.bidu_list a[href]"):
        href = (a.get("href") or "").strip()
        full = _safe_hebei_url(urljoin(HEBEI_ENTRY, href))
        if not full or full in seen:
            continue
        seen.add(full)
        title = _clean_text(a.get("title") or a.get_text(" ", strip=True))
        if len(title) < 2:
            continue
        rows.append({"title": title, "url": full, "publish_date": ""})
        if len(rows) >= max_items:
            break
    if rows:
        return rows
    # 兜底：抓包含“相关知识/必读/指南”等文本链接
    for a in soup.select("a[href]"):
        t = _clean_text(a.get_text(" ", strip=True))
        if not any(k in t for k in ("必读", "相关知识", "指南", "报考", "考试")):
            continue
        href = (a.get("href") or "").strip()
        full = _safe_hebei_url(urljoin(HEBEI_ENTRY, href))
        if not full or full in seen:
            continue
        seen.add(full)
        rows.append({"title": t, "url": full, "publish_date": ""})
        if len(rows) >= max_items:
            break
    return rows


def _safe_hebei_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "zk.hebeea.edu.cn" in host:
        return url
    if "hebeea.edu.cn" in host:
        return url
    return None


def _normalize_date(text: str) -> str:
    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", text or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

