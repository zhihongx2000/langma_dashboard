"""
河南（2）— 自考考生服务平台（固定一级板块）。

入口：`http://zkwb.haeea.cn/ZKService/default.aspx`
一级板块：
- 时间安排（按关键词检索，年份会变化）
- 政策·公告

说明：目标站点常出现 412/拦截，抓取失败时返回说明性占位条目。
"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

HENAN2_ENTRY = "http://zkwb.haeea.cn/ZKService/default.aspx"

LEVEL1_TIME = "时间安排"
LEVEL1_POLICY = "政策·公告"
LEVEL1_SECTIONS: tuple[str, ...] = (LEVEL1_TIME, LEVEL1_POLICY)

TIME_KEYWORDS = ("时间安排", "考试安排", "报考时间", "报名时间", "安排")
POLICY_KEYWORDS = ("政策", "公告", "通知", "简章")


def get_henan2_levels() -> dict:
    empty = [{"name": n, "items": []} for n in LEVEL1_SECTIONS]
    try:
        result = fetch_html(HENAN2_ENTRY, timeout_sec=30, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        all_rows = _parse_links(soup, base_url=result.url)
        time_rows = _filter_rows_by_keywords(all_rows, TIME_KEYWORDS)
        policy_rows = _filter_rows_by_keywords(all_rows, POLICY_KEYWORDS)
        if not time_rows:
            time_rows = _stub_items(
                HENAN2_ENTRY,
                "按关键词检索「时间安排」：年份每年变化，建议在官网页面搜索“时间安排”。",
            )
        if not policy_rows:
            policy_rows = _stub_items(HENAN2_ENTRY, "当前未解析到「政策·公告」列表，请在官网查看。")
        return {
            "source_url": HENAN2_ENTRY,
            "level1": [
                {"name": LEVEL1_TIME, "items": time_rows},
                {"name": LEVEL1_POLICY, "items": policy_rows},
            ],
        }
    except Exception:
        return {
            "source_url": HENAN2_ENTRY,
            "level1": [
                {
                    "name": LEVEL1_TIME,
                    "items": _stub_items(
                        HENAN2_ENTRY,
                        "河南2 站点当前返回 412/拦截；请在官网关键词检索“时间安排”。",
                    ),
                },
                {
                    "name": LEVEL1_POLICY,
                    "items": _stub_items(
                        HENAN2_ENTRY,
                        "河南2 站点当前返回 412/拦截；政策·公告请暂时在官网查看。",
                    ),
                },
            ],
        }


def _parse_links(soup: BeautifulSoup, *, base_url: str, max_items: int = 150) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_henan2_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get_text(" ", strip=True))
        if len(title) < 4:
            continue
        if full in seen:
            continue
        seen.add(full)
        rows.append({"title": title, "url": full, "publish_date": ""})
        if len(rows) >= max_items:
            break
    return rows


def _filter_rows_by_keywords(rows: list[dict], keywords: tuple[str, ...], max_items: int = 80) -> list[dict]:
    picked: list[dict] = []
    for row in rows:
        t = row.get("title", "")
        if any(k in t for k in keywords):
            picked.append(row)
            if len(picked) >= max_items:
                break
    return picked


def _safe_henan2_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "zkwb.haeea.cn" not in host:
        return None
    path = (p.path or "").lower()
    if "/zkservice/" not in path:
        return None
    return url


def _stub_items(section_url: str, note: str) -> list[dict]:
    return [{"title": note, "url": section_url, "publish_date": ""}]


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

