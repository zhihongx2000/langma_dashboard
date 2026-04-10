"""
湖北自考 — 固定一级板块：
- 自学考试
- 社会助学
- 考籍管理
- 自考考务
- 自考计划
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

HUBEI_ENTRY = "https://www.hbea.edu.cn/html/zxks/index.shtml"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("自学考试", "https://www.hbea.edu.cn/html/zxks/index.shtml"),
    ("社会助学", "https://www.hbea.edu.cn/html/shzx/index.shtml"),
    ("考籍管理", "https://www.hbea.edu.cn/html/kjgl/index.shtml"),
    ("自考考务", "https://www.hbea.edu.cn/html/zkkw/index.shtml"),
    ("自考计划", "https://www.hbea.edu.cn/html/zkjh/index.shtml"),
)


def get_hubei_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_hubei_list(soup, base_url=result.url)
        if not items:
            items = _stub_items(f"当前未解析到湖北自考「{display_name}」列表。")
        level1.append({"name": display_name, "items": items})
    return {"source_url": HUBEI_ENTRY, "level1": level1}


def _parse_hubei_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_hubei_content_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get("title") or a.get_text(" ", strip=True))
        title = re.sub(r"\s*(20\d{2}年\d{1,2}月\d{1,2}日)\s*$", "", title)
        if len(title) < 4:
            continue
        if any(k in title for k in ("机构设置", "微信公众号")):
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
                "publish_date": _extract_cn_date(li_text) or _extract_cn_date(title) or _extract_date_from_url(full),
            }
        )
        if len(rows) >= max_items:
            break
    return rows


def _safe_hubei_content_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "hbea.edu.cn" not in host:
        return None
    path = (p.path or "").lower()
    if not path.endswith(".shtml"):
        return None
    if "/html/20" not in path:
        return None
    if path.endswith("/index.shtml"):
        return None
    return url


def _extract_cn_date(text: str) -> str:
    m = re.search(r"(20\d{2})年(\d{1,2})月(\d{1,2})日", text or "")
    if not m:
        return ""
    return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"


def _extract_date_from_url(url: str) -> str:
    m = re.search(r"/(20\d{2})-(\d{2})/\d+\.shtml", (url or "").lower())
    return f"{m.group(1)}-{m.group(2)}-01" if m else ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _stub_items(message: str) -> list[dict]:
    return [{"title": message, "url": HUBEI_ENTRY, "publish_date": ""}]

