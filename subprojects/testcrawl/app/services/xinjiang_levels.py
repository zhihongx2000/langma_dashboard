"""
新疆高等自学考试栏目：一级板块固定为「通知公告」「政策资讯」，
分别对应官网列表页（与侧栏 `tzgg` / `zczx` 一致）。
"""

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

# 名称与顺序由产品规定；URL 与 get.txt 及官网侧栏一致
XINJIANG_LEVEL1_PAGES: tuple[tuple[str, str], ...] = (
    ("通知公告", "https://www.xjzk.gov.cn/zxks/gdjyzxks/tzgg/"),
    ("政策资讯", "https://www.xjzk.gov.cn/zxks/gdjyzxks/zczx/"),
)


def get_xinjiang_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in XINJIANG_LEVEL1_PAGES:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        policy_column = display_name == "政策资讯"
        items = _parse_list_page(soup, base_url=result.url, policy_column=policy_column)
        level1.append({"name": display_name, "items": items})

    return {
        "source_url": XINJIANG_LEVEL1_PAGES[0][1],
        "level1": level1,
    }


def _parse_list_page(
    soup: BeautifulSoup,
    *,
    base_url: str,
    policy_column: bool = False,
) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for li in soup.select("#conts div.tabPanel > ul.list > li"):
        a = li.find("a", href=True)
        if not a:
            continue
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#"):
            continue
        full = _safe_list_url(urljoin(base_url, href), policy_column=policy_column)
        if not full:
            continue

        txt_el = a.find("span", class_="txt")
        time_el = a.find("span", class_="time")
        title = _clean_text(
            txt_el.get_text(" ", strip=True) if txt_el else a.get_text(" ", strip=True)
        )
        if not title:
            continue

        publish_date = _clean_text(time_el.get_text(" ", strip=True) if time_el else "")
        if full in seen:
            continue
        seen.add(full)
        rows.append({"title": title, "url": full, "publish_date": publish_date})
    return rows


def _safe_list_url(url: str, *, policy_column: bool) -> str | None:
    """列表页仅保留考试院本站；政策资讯另收录教育部教育考试院自考专题（neea）外链。"""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None
    host = parsed.netloc.lower()
    if "xjzk.gov.cn" in host:
        return url
    if policy_column and host.endswith("neea.edu.cn"):
        return url
    return None


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()
