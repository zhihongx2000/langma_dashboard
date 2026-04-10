"""
广东2（eeagd.edu.cn /selfec）— 固定一级板块：
- 专业计划
- 助学管理
- 考务管理
- 考籍管理
- 其他公告
"""

from __future__ import annotations

import re
import requests
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

GUANGDONG2_ENTRY = "https://www.eeagd.edu.cn/selfec/"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("专业计划", "https://www.eeagd.edu.cn/selfec/notice-list.html?type=zyjh"),
    ("助学管理", "https://www.eeagd.edu.cn/selfec/notice-list.html?type=zxgl"),
    ("考务管理", "https://www.eeagd.edu.cn/selfec/notice-list.html?type=kwgl"),
    ("考籍管理", "https://www.eeagd.edu.cn/selfec/notice-list.html?type=kjgl"),
    ("其他公告", "https://www.eeagd.edu.cn/selfec/notice-list.html?type=qtgg"),
)


def get_guangdong2_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        items = _fetch_notice_api_items(type_code=_type_from_url(page_url))
        if not items:
            result = fetch_html(page_url, timeout_sec=25, prefer_browser=True)
            soup = BeautifulSoup(result.html, "lxml")
            items = _parse_notice_list(soup, base_url=result.url)
        if not items:
            if display_name == "助学管理":
                items = _stub_items(
                    "「助学管理」栏目当前官网列表为空（notice-list?type=zxgl 无数据），请稍后在官网查看。"
                )
            else:
                items = _stub_items(f"当前未解析到广东2「{display_name}」列表。")
        level1.append({"name": display_name, "items": items})
    return {"source_url": GUANGDONG2_ENTRY, "level1": level1}


def _parse_notice_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_gd2_detail_url(urljoin(base_url, href))
        if not full:
            continue
        title = _clean_text(a.get("title") or a.get_text(" ", strip=True))
        title = re.sub(r"\s+\d{4}-\d{2}-\d{2}\s*$", "", title)
        if len(title) < 4:
            continue
        if "无公告数据" in title:
            continue
        if full in seen:
            continue
        seen.add(full)
        date_span = a.select_one(".news-date")
        publish = ""
        if date_span is not None:
            publish = _extract_date_like(_clean_text(date_span.get_text(" ", strip=True)))
        if not publish:
            publish = _extract_date_like(_clean_text(a.get_text(" ", strip=True)))
        rows.append({"title": title, "url": full, "publish_date": publish})
        if len(rows) >= max_items:
            break
    return rows


def _fetch_notice_api_items(type_code: str, max_items: int = 120) -> list[dict]:
    """
    eeagd 自考列表页实际通过 JS 调用 /selfec/notices 返回 JSON。
    当该接口可用时优先使用，避免静态 HTML 无列表导致全量占位。
    """
    if not type_code:
        return []
    try:
        response = requests.post(
            "https://www.eeagd.edu.cn/selfec/notices",
            json={"type": type_code, "page": 1, "pageSize": max_items},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []
    return _rows_from_notice_payload(payload, max_items=max_items)


def _rows_from_notice_payload(payload: dict, *, max_items: int = 120) -> list[dict]:
    data = payload.get("data") if isinstance(payload, dict) else None
    notices = data.get("notices") if isinstance(data, dict) else None
    if not isinstance(notices, list):
        return []

    rows: list[dict] = []
    seen: set[str] = set()
    for notice in notices:
        if not isinstance(notice, dict):
            continue
        ggxh = notice.get("ggxh")
        title = _clean_text(str(notice.get("bt") or ""))
        if not ggxh or len(title) < 4:
            continue
        full = f"https://www.eeagd.edu.cn/selfec/notice-detail.html?ggxh={ggxh}"
        if full in seen:
            continue
        seen.add(full)
        publish = _extract_date_like(_clean_text(str(notice.get("gxsj") or "")))
        rows.append({"title": title, "url": full, "publish_date": publish})
        if len(rows) >= max_items:
            break
    return rows


def _type_from_url(url: str) -> str:
    p = urlparse(url)
    q = (p.query or "").lower()
    m = re.search(r"(?:^|&)type=([a-z0-9_]+)", q)
    return m.group(1) if m else ""


def _safe_gd2_detail_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "eeagd.edu.cn" not in host:
        return None
    path = (p.path or "").lower()
    if "notice-detail" not in path:
        return None
    q = (p.query or "").lower()
    if "ggxh=" not in q:
        return None
    return url


def _extract_date_like(text: str) -> str:
    m = re.search(r"(20\d{2})[-/](\d{2})[-/](\d{2})", text or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _stub_items(message: str) -> list[dict]:
    return [{"title": message, "url": GUANGDONG2_ENTRY, "publish_date": ""}]
