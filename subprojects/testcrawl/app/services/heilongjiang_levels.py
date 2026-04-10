"""
黑龙江省招生考试院—自学考试频道。

一级概念：自考频道（入口为 zxxx_149）。
二级固定栏目顺序与官网左侧导航一致；各栏文章由各列表页解析。
"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

ZK_BASE = "https://www.lzk.hl.cn/zk"

# 与 get.txt 入口一致；频道首页
HEILONGJIANG_ZX_CHANNEL_ROOT = f"{ZK_BASE}/zxxx_149/"

# （展示名，列表页 URL）
LEVEL2_SECTIONS: tuple[tuple[str, str], ...] = (
    ("最新信息", f"{ZK_BASE}/zxxx_149/"),
    ("自考信息", f"{ZK_BASE}/zkxx/"),
    ("政策法规", f"{ZK_BASE}/zcfg_140/"),
    ("成绩发布", f"{ZK_BASE}/cjfb_141/"),
    ("考生问答", f"{ZK_BASE}/kswd_142/"),
    ("试题大全", f"{ZK_BASE}/stdq_143/"),
    ("考试指南", f"{ZK_BASE}/kszn/"),
    ("试题笔记", f"{ZK_BASE}/stbj/"),
    ("社会助学", f"{ZK_BASE}/shzx/"),
    ("计划教材", f"{ZK_BASE}/jhjc/"),
)

CHANNEL_NAME = "自考频道"


def get_heilongjiang_levels() -> dict:
    level1: list[dict] = []
    for display_name, list_url in LEVEL2_SECTIONS:
        result = fetch_html(list_url, timeout_sec=25, prefer_browser=False)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_list_table(soup, base_url=result.url)
        level1.append({"name": display_name, "items": items})

    return {
        "source_url": HEILONGJIANG_ZX_CHANNEL_ROOT,
        "channel_name": CHANNEL_NAME,
        "level1": level1,
    }


def _parse_list_table(soup: BeautifulSoup, *, base_url: str, max_items: int = 80) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 2:
            continue
        a = tds[0].find("a", href=True)
        if not a:
            continue
        href = (a.get("href") or "").strip()
        if not href or "javascript" in href.lower():
            continue
        if a.get("target") != "_blank":
            continue
        low = href.lower()
        if not (low.endswith(".htm") or low.endswith(".html") or low.endswith(".shtml")):
            continue

        full = urljoin(base_url, href)
        safe = _safe_hlj_url(full)
        if not safe:
            continue

        title = _clean_text(a.get_text(" ", strip=True))
        if len(title) < 2:
            continue

        publish_date = _clean_text(tds[1].get_text(" ", strip=True))
        if safe in seen:
            continue
        seen.add(safe)
        rows.append({"title": title, "url": safe, "publish_date": publish_date})
        if len(rows) >= max_items:
            break
    return rows


def _safe_hlj_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None
    host = parsed.netloc.lower()
    if "lzk.hl.cn" not in host:
        return None
    return url


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()
