"""
北京教育考试院 — 自学考试（固定一级板块）。

一级板块：
- 信息发布台
- 自考政策
- 近期业务
- 快速通道
- 必备知识
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

BEIJING_ZXKS_ENTRY = "https://www.bjeea.cn/html/selfstudy/index.html"

LEVEL1_NAMES: tuple[str, ...] = (
    "信息发布台",
    "自考政策",
    "近期业务",
    "快速通道",
    "必备知识",
)


def get_beijing_levels() -> dict:
    result = fetch_html(BEIJING_ZXKS_ENTRY, timeout_sec=25, prefer_browser=True)
    soup = BeautifulSoup(result.html, "lxml")

    info_rows = _parse_info_or_policy(soup, heading="信息发布台")
    policy_rows = _parse_info_or_policy(soup, heading="自考政策")
    recent_rows = _parse_side_section(soup, heading="近期业务", ul_selector="ul.rc-ulist")
    quick_rows = _parse_side_section(soup, heading="快速通道", ul_selector="ul.sub-navbox")
    knowledge_rows = _parse_side_section(soup, heading="必备知识", ul_selector="ul.sub-navbox")

    payload = [
        {"name": "信息发布台", "items": info_rows},
        {"name": "自考政策", "items": policy_rows},
        {"name": "近期业务", "items": recent_rows},
        {"name": "快速通道", "items": quick_rows},
        {"name": "必备知识", "items": knowledge_rows},
    ]
    return {"source_url": BEIJING_ZXKS_ENTRY, "level1": payload}


def _parse_info_or_policy(soup: BeautifulSoup, *, heading: str, max_items: int = 80) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for row in soup.select("div.row.m-t-20"):
        tit = row.select_one("div.com-tit span")
        if not tit:
            continue
        if _clean_text(tit.get_text(" ", strip=True)) != heading:
            continue
        ul = row.select_one("ul.com-list")
        if not ul:
            ul = row.find_next("ul", class_="com-list")
        if not ul:
            continue
        rows.extend(_collect_rows_from_ul(ul, seen=seen, max_items=max_items))
        if rows:
            break
    return rows


def _parse_side_section(soup: BeautifulSoup, *, heading: str, ul_selector: str, max_items: int = 80) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for span in soup.select("span.fz24"):
        if _clean_text(span.get_text(" ", strip=True)) != heading:
            continue
        innert = span.find_parent("div", class_="innert")
        if not innert:
            continue
        block = innert.find_parent("div")
        if not block:
            continue
        nxt_ul = block.find_next("ul")
        while nxt_ul and not nxt_ul.select_one("a[href]"):
            nxt_ul = nxt_ul.find_next("ul")
        if not nxt_ul:
            continue
        if ul_selector and ul_selector.startswith("ul."):
            need_cls = ul_selector.replace("ul.", "")
            if need_cls not in (nxt_ul.get("class") or []):
                # 对快速通道/必备知识，优先 class 匹配；不匹配则继续找
                tmp = nxt_ul.find_next("ul")
                found = None
                while tmp:
                    classes = tmp.get("class") or []
                    if need_cls in classes and tmp.select_one("a[href]"):
                        found = tmp
                        break
                    tmp = tmp.find_next("ul")
                if found:
                    nxt_ul = found
        rows.extend(_collect_rows_from_ul(nxt_ul, seen=seen, max_items=max_items))
        if rows:
            break
    return rows


def _collect_rows_from_ul(ul, *, seen: set[str], max_items: int) -> list[dict]:
    out: list[dict] = []
    for li in ul.select("li"):
        a = li.find("a", href=True)
        if not a:
            continue
        href = (a.get("href") or "").strip()
        title = _clean_text(a.get("title") or a.get_text(" ", strip=True))
        if not href or len(title) < 2:
            continue
        full = _safe_beijing_url(urljoin(BEIJING_ZXKS_ENTRY, href))
        if not full:
            continue
        if full in seen:
            continue
        seen.add(full)
        date_el = li.select_one(".li-time")
        date_text = _clean_text(date_el.get_text(" ", strip=True) if date_el else "")
        out.append({"title": _strip_inline_noise(title), "url": full, "publish_date": _normalize_date(date_text)})
        if len(out) >= max_items:
            break
    return out


def _safe_beijing_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if not host.endswith("bjeea.cn"):
        return None
    return url


def _strip_inline_noise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_date(text: str) -> str:
    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", text or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

