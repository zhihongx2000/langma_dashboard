"""
江西自考 — 固定一级板块：
- 考试动态
- 通知公告
- 常见问答
"""

from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

JIANGXI_ENTRY = "http://www.jxeea.cn/jxsjyksy/zxks55/list.html"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("考试动态", "http://www.jxeea.cn/jxsjyksy/ksdt73/list.html"),
    ("通知公告", "http://www.jxeea.cn/jxsjyksy/tzgg11/list.html"),
    ("常见问答", "http://www.jxeea.cn/jxsjyksy/cjwd10/list.html"),
)


def get_jiangxi_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_jiangxi_list(soup, base_url=result.url)
        if not items:
            items = _stub_items(f"当前未解析到江西自考「{display_name}」列表，可先从官网栏目页手动进入查看。")
        level1.append({"name": display_name, "items": items})
    return {"source_url": JIANGXI_ENTRY, "level1": level1}


def _parse_jiangxi_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_jiangxi_content_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get("title") or a.get_text(" ", strip=True))
        if len(title) < 4:
            continue
        if full in seen:
            continue
        seen.add(full)
        li_text = ""
        li = a.find_parent("li")
        if li is not None:
            li_text = _clean_text(li.get_text(" ", strip=True))
        rows.append({"title": title, "url": full, "publish_date": _extract_date_like(li_text) or _extract_date_like(title)})
        if len(rows) >= max_items:
            break
    if not rows:
        rows = _parse_jiangxi_list_from_script(soup, base_url=base_url, max_items=max_items)
    return rows


def _parse_jiangxi_list_from_script(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for script in soup.select("script"):
        text = script.get_text(" ", strip=False) or ""
        if "articleList" not in text or "listData" not in text:
            continue
        for article in _extract_article_list_objects(text):
            full = _article_pc_url(article, base_url=base_url)
            if not full or full in seen:
                continue
            raw_title = str(article.get("showTitle") or article.get("title") or "")
            title = _clean_text(BeautifulSoup(raw_title, "lxml").get_text(" ", strip=True))
            if len(title) < 4:
                continue
            seen.add(full)
            rows.append(
                {
                    "title": title,
                    "url": full,
                    "publish_date": _extract_date_like(str(article.get("pubDate") or "")),
                }
            )
            if len(rows) >= max_items:
                return rows
    return rows


def _extract_article_list_objects(script_text: str) -> list[dict]:
    key = re.search(r"articleList\s*:\s*\[", script_text)
    if not key:
        return []
    start = script_text.find("[", key.start())
    if start < 0:
        return []
    payload = _extract_balanced_json_array(script_text, start)
    if not payload:
        return []
    try:
        data = json.loads(payload)
    except Exception:
        return []
    return [x for x in data if isinstance(x, dict)]


def _extract_balanced_json_array(text: str, start: int) -> str:
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return ""


def _article_pc_url(article: dict, *, base_url: str) -> str | None:
    urls_value = article.get("urls")
    pc = ""
    if isinstance(urls_value, str):
        try:
            parsed = json.loads(urls_value)
        except Exception:
            parsed = {}
        if isinstance(parsed, dict):
            pc = str(parsed.get("pc") or "")
    elif isinstance(urls_value, dict):
        pc = str(urls_value.get("pc") or "")
    if not pc:
        return None
    return _safe_jiangxi_content_url(urljoin(base_url, pc))


def _safe_jiangxi_content_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "jxeea.cn" not in host:
        return None
    path = (p.path or "").lower()
    if not path.endswith(".html"):
        return None
    allowed = ("/jxsjyksy/ksdt73/content/content_", "/jxsjyksy/tzgg11/content/content_", "/jxsjyksy/cjwd10/content/content_")
    if not any(prefix in path for prefix in allowed):
        return None
    return url


def _extract_date_like(text: str) -> str:
    m = re.search(r"(20\d{2})[-/](\d{2})[-/](\d{2})", text or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _stub_items(message: str) -> list[dict]:
    return [{"title": message, "url": JIANGXI_ENTRY, "publish_date": ""}]

