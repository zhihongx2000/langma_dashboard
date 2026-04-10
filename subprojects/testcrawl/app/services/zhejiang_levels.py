"""
浙江省教育考试院 — 自学考试固定一级板块。
"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

ZJ_SOURCE_URL = "https://www.zjzs.net/col/col21/index.html"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("最新消息", "https://www.zjzs.net/col/col21/index.html"),
    ("政策文件", "https://www.zjzs.net/col/col41/index.html"),
    ("专业计划", "https://www.zjzs.net/col/col42/index.html"),
    ("考试报名", "https://www.zjzs.net/col/col43/index.html"),
    ("转考免考", "https://www.zjzs.net/col/col324/index.html"),
    ("毕业办理", "https://www.zjzs.net/col/col325/index.html"),
)


def get_zhejiang_levels() -> dict:
    level1: list[dict] = []
    for name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_zj_list(soup, base_url=result.url)
        level1.append({"name": name, "items": items})
    return {"source_url": ZJ_SOURCE_URL, "level1": level1}


def _parse_zj_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for li in soup.select("li"):
        a = li.find("a", href=True)
        if not a:
            continue
        href = (a.get("href") or "").strip()
        title = _clean_text(a.get("title") or a.get_text(" ", strip=True))
        if not href or len(title) < 4:
            continue
        full = _safe_zj_url(urljoin(base_url, href))
        if not full:
            continue
        if full in seen:
            continue
        seen.add(full)
        publish_date = _extract_date_from_li(li.get_text(" ", strip=True))
        rows.append({"title": title, "url": full, "publish_date": publish_date})
        if len(rows) >= max_items:
            break
    return rows


def _safe_zj_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if not host.endswith("zjzs.net"):
        return None
    path = (p.path or "").lower()
    if path.startswith("/art/") or path.startswith("/col/"):
        return url
    return None


def _extract_date_from_li(text: str) -> str:
    import re

    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", text or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

