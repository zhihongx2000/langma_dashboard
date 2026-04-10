"""
湖南自考 — 固定一级板块：
- 2026年考试日程
- 最新消息
- 通知公告
- 自考政策
- 开考课程计划
- 考试大纲
- 考试计划
"""

from __future__ import annotations

import re
import subprocess
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from app.services.fetcher import fetch_html

HUNAN_ENTRY = "https://nzkks.hneao.cn/student_anon/home"
_NOTICE_LIST_API = "https://nzkks.hneao.cn/proxy/admin_anon/v1/pubManage/baseNoticeCommon/list"
_SCHEDULE_API = "https://nzkks.hneao.cn/proxy/student_anon/v1/pubmanage/gatewaySettingStu/queryBaseExamScheduleSetting"
SECTION_NAMES = (
    "2026年考试日程",
    "最新消息",
    "通知公告",
    "自考政策",
    "开考课程计划",
    "考试大纲",
    "考试计划",
)


def get_hunan_levels() -> dict:
    # 优先使用官网接口，避免首页前端渲染导致静态抓取为空。
    api_rows = _fetch_hunan_sections_from_api(timeout_sec=30)
    if api_rows:
        return {"source_url": HUNAN_ENTRY, "level1": api_rows}

    try:
        base_url, html = _fetch_hunan_html(HUNAN_ENTRY, timeout_sec=30)
    except Exception:
        return {
            "source_url": HUNAN_ENTRY,
            "level1": [{"name": n, "items": _stub_items(f"当前未解析到湖南自考「{n}」列表。")} for n in SECTION_NAMES],
        }

    soup = BeautifulSoup(html, "lxml")
    level1 = [
        {"name": "2026年考试日程", "items": _parse_schedule_items(soup, base_url=base_url)},
        {"name": "最新消息", "items": _parse_latest_items(soup, base_url=base_url)},
    ]
    first_tab = _extract_from_tab_group(soup, ("通知公告", "自考政策"), base_url=base_url)
    second_tab = _extract_from_tab_group(soup, ("开考课程计划", "考试大纲", "考试计划"), base_url=base_url)
    level1.extend(
        [
            {"name": "通知公告", "items": first_tab.get("通知公告") or _stub_items("当前未解析到湖南自考「通知公告」列表。")},
            {"name": "自考政策", "items": first_tab.get("自考政策") or _stub_items("当前未解析到湖南自考「自考政策」列表。")},
            {"name": "开考课程计划", "items": second_tab.get("开考课程计划") or _stub_items("当前未解析到湖南自考「开考课程计划」列表。")},
            {"name": "考试大纲", "items": second_tab.get("考试大纲") or _stub_items("当前未解析到湖南自考「考试大纲」列表。")},
            {"name": "考试计划", "items": second_tab.get("考试计划") or _stub_items("当前未解析到湖南自考「考试计划」列表。")},
        ]
    )
    return {"source_url": base_url, "level1": level1}


def _fetch_hunan_sections_from_api(*, timeout_sec: int = 30) -> list[dict]:
    try:
        notices_resp = requests.post(
            _NOTICE_LIST_API,
            data="{}",
            headers={"Content-Type": "application/json"},
            timeout=timeout_sec,
            verify=False,
        )
        notices_resp.raise_for_status()
        notices_json = notices_resp.json()

        schedule_resp = requests.post(
            _SCHEDULE_API,
            json={},
            timeout=timeout_sec,
            verify=False,
        )
        schedule_resp.raise_for_status()
        schedule_json = schedule_resp.json()
    except Exception:
        return []

    level1 = []
    schedule_items = _schedule_from_api(schedule_json)
    level1.append({"name": "2026年考试日程", "items": schedule_items or _stub_items("当前未解析到湖南自考「2026年考试日程」列表。")})

    latest_items = _latest_from_api(notices_json)
    level1.append({"name": "最新消息", "items": latest_items or _stub_items("当前未解析到湖南自考「最新消息」列表。")})

    notice_map = _notice_map_from_api(notices_json)
    level1.extend(
        [
            {"name": "通知公告", "items": notice_map.get("1") or _stub_items("当前未解析到湖南自考「通知公告」列表。")},
            {"name": "自考政策", "items": notice_map.get("2") or _stub_items("当前未解析到湖南自考「自考政策」列表。")},
            {"name": "开考课程计划", "items": notice_map.get("5") or _stub_items("当前未解析到湖南自考「开考课程计划」列表。")},
            {"name": "考试大纲", "items": notice_map.get("3") or _stub_items("当前未解析到湖南自考「考试大纲」列表。")},
            {"name": "考试计划", "items": notice_map.get("4") or _stub_items("当前未解析到湖南自考「考试计划」列表。")},
        ]
    )
    return level1


def _schedule_from_api(payload: dict) -> list[dict]:
    rows = payload.get("result") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return []
    out: list[dict] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        title = _clean_text(str(r.get("content") or ""))
        if not title:
            continue
        start = _extract_date_like(str(r.get("startDate") or ""))
        end = _extract_date_like(str(r.get("endDate") or ""))
        publish = f"{start} ~ {end}" if start and end else (start or end)
        out.append({"title": title, "url": HUNAN_ENTRY, "publish_date": publish})
    return out


def _latest_from_api(payload: dict) -> list[dict]:
    result = payload.get("result") if isinstance(payload, dict) else None
    if not isinstance(result, dict):
        return []
    one = result.get("newOne")
    if not isinstance(one, dict):
        return []
    nid = one.get("id")
    title = _clean_text(str(one.get("title") or ""))
    if not nid or not title:
        return []
    date = _extract_date_like(str(one.get("auditDate") or one.get("createTime") or ""))
    return [{"title": title, "url": f"https://nzkks.hneao.cn/student_anon/noticeDetail?id={nid}", "publish_date": date}]


def _notice_map_from_api(payload: dict) -> dict[str, list[dict]]:
    result = payload.get("result") if isinstance(payload, dict) else None
    mp = result.get("map") if isinstance(result, dict) else None
    if not isinstance(mp, dict):
        return {}
    out: dict[str, list[dict]] = {}
    for k, arr in mp.items():
        if not isinstance(arr, list):
            continue
        rows: list[dict] = []
        for r in arr:
            if not isinstance(r, dict):
                continue
            nid = r.get("id")
            title = _clean_text(str(r.get("title") or ""))
            if not nid or not title:
                continue
            date = _extract_date_like(str(r.get("auditDate") or r.get("createTime") or ""))
            rows.append(
                {
                    "title": title,
                    "url": f"https://nzkks.hneao.cn/student_anon/noticeDetail?id={nid}",
                    "publish_date": date,
                }
            )
        out[str(k)] = rows
    return out


def _fetch_hunan_html(url: str, *, timeout_sec: int = 30) -> tuple[str, str]:
    """
    nzkks.hneao.cn 在部分环境中 requests 会证书校验失败。
    优先走 fetch_html；失败时回退系统 curl 获取 HTML。
    """
    try:
        result = fetch_html(url, timeout_sec=timeout_sec, prefer_browser=True)
        return result.url, result.html
    except Exception:
        return url, _fetch_with_curl(url, timeout_sec=timeout_sec)


def _fetch_with_curl(url: str, *, timeout_sec: int = 30) -> str:
    proc = subprocess.run(
        ["curl.exe", "-L", url, "--max-time", str(timeout_sec)],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed: code={proc.returncode}")
    return proc.stdout.decode("utf-8", errors="replace")


def _parse_schedule_items(soup: BeautifulSoup, *, base_url: str) -> list[dict]:
    rows: list[dict] = []
    for div in soup.select(".ksrc .itemInfo"):
        spans = div.select("span")
        if len(spans) < 2:
            continue
        time_text = _clean_text(spans[0].get_text(" ", strip=True))
        label = _clean_text(spans[1].get_text(" ", strip=True))
        if not label:
            continue
        rows.append({"title": label, "url": base_url, "publish_date": time_text})
    return rows or _stub_items("当前未解析到湖南自考「2026年考试日程」列表。")


def _parse_latest_items(soup: BeautifulSoup, *, base_url: str) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for node in soup.select("#newone .new-notice-item"):
        onclick = (node.get("onclick") or "").strip()
        url = _url_from_onclick(onclick, base_url=base_url)
        title_text = _clean_text(node.get_text(" ", strip=True))
        title = re.sub(r"\s*发布日期.*$", "", title_text).strip()
        date = _extract_date_like(title_text)
        if not title:
            continue
        key = url or title
        if key in seen:
            continue
        seen.add(key)
        rows.append({"title": title, "url": url or base_url, "publish_date": date})
    return rows or _stub_items("当前未解析到湖南自考「最新消息」列表。")


def _extract_from_tab_group(
    soup: BeautifulSoup,
    title_tuple: tuple[str, ...],
    *,
    base_url: str,
) -> dict[str, list[dict]]:
    for box in soup.select("div.divContent.layui-tab.layui-tab-brief"):
        titles = tuple(_clean_text(li.get_text(" ", strip=True)) for li in box.select("ul.layui-tab-title > li"))
        if titles != title_tuple:
            continue
        tab_items = box.select("div.layui-tab-content > div.layui-tab-item")
        out: dict[str, list[dict]] = {}
        for idx, name in enumerate(titles):
            out[name] = _parse_tab_item(tab_items[idx] if idx < len(tab_items) else None, base_url=base_url)
        return out
    return {name: [] for name in title_tuple}


def _parse_tab_item(tab_item: Tag | None, *, base_url: str) -> list[dict]:
    if tab_item is None:
        return []
    rows: list[dict] = []
    seen: set[str] = set()

    for row in tab_item.select(".notice-item"):
        payload = _row_to_payload(row, base_url=base_url)
        if not payload:
            continue
        key = payload["url"] or payload["title"]
        if key in seen:
            continue
        seen.add(key)
        rows.append(payload)

    if not rows:
        for node in tab_item.select('[onclick*="noticeDetail"]'):
            payload = _row_to_payload(node, base_url=base_url)
            if not payload:
                continue
            key = payload["url"] or payload["title"]
            if key in seen:
                continue
            seen.add(key)
            rows.append(payload)
    return rows


def _row_to_payload(node: Tag, *, base_url: str) -> dict | None:
    onclick = (node.get("onclick") or "").strip()
    if not onclick:
        clickable = node.select_one('[onclick*="noticeDetail"]')
        onclick = (clickable.get("onclick") or "").strip() if clickable else ""
    url = _url_from_onclick(onclick, base_url=base_url) if onclick else ""
    title = ""
    date = ""

    title_node = node.select_one(".title, .name, .notice-title")
    date_node = node.select_one(".date, .time, .notice-date")
    if title_node is not None:
        title = _clean_text(title_node.get_text(" ", strip=True))
    if date_node is not None:
        date = _extract_date_like(_clean_text(date_node.get_text(" ", strip=True)))

    if not title:
        text = _clean_text(node.get_text(" ", strip=True))
        text = re.sub(r"^\d{1,2}\s+\d{4}\.\d{2}\s*", "", text)
        text = re.sub(r"^·\s*", "", text)
        if "·" in text:
            parts = [p.strip() for p in text.split("·") if p.strip()]
            if parts:
                title = parts[0]
            if len(parts) > 1 and not date:
                date = _extract_date_like(parts[-1])
        else:
            title = re.sub(r"\s+\d{4}[-/.]\d{2}[-/.]\d{2}$", "", text).strip()
        if not date:
            date = _extract_date_like(text)

    if not title:
        return None
    return {"title": title, "url": url or base_url, "publish_date": date}


def _url_from_onclick(onclick: str, *, base_url: str) -> str:
    m = re.search(r"window\.location\.href=['\"](?P<url>[^'\"]+)['\"]", onclick or "")
    if not m:
        return ""
    full = urljoin(base_url, m.group("url"))
    return _safe_hunan_url(full) or ""


def _safe_hunan_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "nzkks.hneao.cn" not in host:
        return None
    return url


def _extract_date_like(text: str) -> str:
    t = text or ""
    m = re.search(r"(20\d{2})[-/.](\d{2})[-/.](\d{2})", t)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m2 = re.search(r"(20\d{2})年(\d{1,2})月(\d{1,2})日", t)
    if m2:
        return f"{m2.group(1)}-{int(m2.group(2)):02d}-{int(m2.group(3)):02d}"
    m3 = re.search(r"(20\d{2})\.(\d{2})", t)
    if m3:
        return f"{m3.group(1)}-{m3.group(2)}-01"
    return ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _stub_items(message: str) -> list[dict]:
    return [{"title": message, "url": HUNAN_ENTRY, "publish_date": ""}]

