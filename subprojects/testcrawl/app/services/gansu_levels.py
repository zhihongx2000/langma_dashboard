"""
甘肃省教育考试院 — 自学考试（甘肃1 入口 zixuekaoshi）固定一级板块：通知公告、政策规定。

官网「自学考试」下：通知公告 → tongzhigonggao631，政策规定 → baokaojianzhang（页面标题均为 自学考试-…）。
列表为 `ul.newslist li`，链接多为站内 `/zixuekaoshi/*.html`。
"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

# get.txt 中甘肃第一条；访问会跳转到通知列表属正常
GANSU_ZIXUE_ENTRY = "https://www.ganseea.cn/zixuekaoshi/"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("通知公告", "https://www.ganseea.cn/tongzhigonggao631/"),
    ("政策规定", "https://www.ganseea.cn/baokaojianzhang/"),
)


def get_gansu_levels() -> dict:
    level1: list[dict] = []
    for display_name, list_url in LEVEL1_SECTIONS:
        result = fetch_html(list_url, timeout_sec=25, prefer_browser=False)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_newslist(soup, base_url=result.url)
        level1.append({"name": display_name, "items": items})

    return {"source_url": GANSU_ZIXUE_ENTRY, "level1": level1}


def _parse_newslist(soup: BeautifulSoup, *, base_url: str, max_items: int = 80) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for li in soup.select("ul.newslist li"):
        a = li.find("a", href=True)
        if not a:
            continue
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or "javascript:" in href.lower():
            continue

        full = urljoin(base_url, href)
        if not _safe_gansu_site_url(full):
            continue

        title = _clean_text(a.get("title") or a.get_text(" ", strip=True))
        bracket = title.find("]")
        if bracket != -1 and title.startswith("["):
            title = _clean_text(title[bracket + 1 :])
        if len(title) < 2:
            continue

        span = li.find("span")
        publish_date = _clean_text(span.get_text(" ", strip=True)) if span else ""

        if full in seen:
            continue
        seen.add(full)
        rows.append({"title": title, "url": full, "publish_date": publish_date})
        if len(rows) >= max_items:
            break
    return rows


def _safe_gansu_site_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None
    host = parsed.netloc.lower()
    if "ganseea.cn" not in host:
        return None
    return url


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()
