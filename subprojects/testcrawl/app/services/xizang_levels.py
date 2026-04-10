"""
西藏自学考试门户一级板块：固定为「通知公告」「政策法规」「招生简章」，
对应自考频道页中 `.title-tzgg` / `.title-zcfg` / `.title-zsjz` 及其后相邻列表。
"""

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

XIZANG_ROOT_URL = "http://zsks.edu.xizang.gov.cn/92/index.html"

# 名称与顺序由产品规定，与页面栏目一致
LEVEL1_SPEC: tuple[tuple[str, str], ...] = (
    ("通知公告", "div.title-tzgg"),
    ("政策法规", "div.title-zcfg"),
    ("招生简章", "div.title-zsjz"),
)


def get_xizang_levels() -> dict:
    result = fetch_html(XIZANG_ROOT_URL, timeout_sec=25, prefer_browser=True)
    soup = BeautifulSoup(result.html, "lxml")

    level1 = []
    for display_name, selector in LEVEL1_SPEC:
        marker = soup.select_one(selector)
        ul = marker.find_next_sibling("ul") if marker else None
        items = _collect_list_links(ul, base_url=result.url) if ul else []
        level1.append({"name": display_name, "items": items})

    return {"source_url": result.url, "level1": level1}


def _collect_list_links(ul, *, base_url: str) -> list[dict]:
    rows = []
    seen: set[str] = set()
    for li in ul.find_all("li", recursive=False):
        a = li.find("a", href=True)
        if not a:
            continue
        title = _clean_text(a.get_text(" ", strip=True))
        href = (a.get("href") or "").strip()
        if not title or not href:
            continue
        full = _safe_url(urljoin(base_url, href))
        if not full:
            continue
        date_el = li.find("span", class_="date")
        publish_date = _clean_text(date_el.get_text(" ", strip=True) if date_el else "")
        if full in seen:
            continue
        seen.add(full)
        rows.append({"title": title, "url": full, "publish_date": publish_date})
    return rows


def _safe_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None
    host = parsed.netloc.lower()
    if "xizang.gov.cn" not in host:
        return None
    return url


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()
