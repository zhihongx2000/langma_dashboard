"""
吉林省教育考试院 — 自学考试（固定一级板块）。

入口：`https://www.jleea.com.cn/front/channel/9944`
一级板块：
- 通知公告
- 政策法规
- 常见问答

实现方式：直接调用站点前端同源接口
`/server-front/front/content/tabList`，按 channelPaths 拉取稳定数据。
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.services.http_client import build_session

JILIN_ENTRY = "https://www.jleea.com.cn/front/channel/9944"

LEVEL1_NOTICE = "通知公告"
LEVEL1_POLICY = "政策法规"
LEVEL1_FAQ = "常见问答"
LEVEL1_SECTIONS: tuple[str, ...] = (LEVEL1_NOTICE, LEVEL1_POLICY, LEVEL1_FAQ)

# 由页面内脚本确认：
# - gdjyzxks_tzgg -> 通知公告
# - gdjyzxks_ksdt -> 政策法规
# - gdjyzxks_cjwd -> 常见问答
CHANNEL_PATHS: tuple[tuple[str, str], ...] = (
    (LEVEL1_NOTICE, "gdjyzxks_tzgg"),
    (LEVEL1_POLICY, "gdjyzxks_ksdt"),
    (LEVEL1_FAQ, "gdjyzxks_cjwd"),
)
TABLIST_API = "https://www.jleea.com.cn/server-front/front/content/tabList"


def get_jilin_levels() -> dict:
    try:
        session = build_session()
        session.headers.update(
            {
                "Referer": JILIN_ENTRY,
                "Accept": "application/json, text/plain, */*",
            }
        )
        block_rows: dict[str, list[dict]] = {}
        for name, channel_path in CHANNEL_PATHS:
            block_rows[name] = _fetch_tab_list(session, channel_path=channel_path, size=20)
            if not block_rows[name]:
                block_rows[name] = _stub_items(f"当前未解析到吉林自考{name}列表。")
        return {
            "source_url": JILIN_ENTRY,
            "level1": [
                {"name": LEVEL1_NOTICE, "items": block_rows[LEVEL1_NOTICE]},
                {"name": LEVEL1_POLICY, "items": block_rows[LEVEL1_POLICY]},
                {"name": LEVEL1_FAQ, "items": block_rows[LEVEL1_FAQ]},
            ],
        }
    except Exception:
        return {
            "source_url": JILIN_ENTRY,
            "level1": [
                {"name": LEVEL1_NOTICE, "items": _stub_items("吉林站点访问失败，暂无法抓取通知公告。")},
                {"name": LEVEL1_POLICY, "items": _stub_items("吉林站点访问失败，暂无法抓取政策法规。")},
                {"name": LEVEL1_FAQ, "items": _stub_items("吉林站点访问失败，暂无法抓取常见问答。")},
            ],
        }


def _fetch_tab_list(session, *, channel_path: str, size: int = 20) -> list[dict]:
    resp = session.get(
        TABLIST_API,
        params={
            "isStatic": "false",
            "size": str(size),
            "channelPaths": channel_path,
            "orderBy": "0",
        },
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if str(payload.get("code", "")).strip() != "00000 00000":
        return []
    data = payload.get("data") or []
    if not isinstance(data, list) or not data:
        return []
    contents = data[0].get("contents") or []
    if not isinstance(contents, list):
        return []

    rows: list[dict] = []
    seen: set[str] = set()
    for item in contents:
        if not isinstance(item, dict):
            continue
        full = _safe_jilin_content_url(str(item.get("url") or "").strip())
        if not full:
            continue
        title = _clean_text(str(item.get("title") or "").strip())
        if len(title) < 4:
            continue
        if full in seen:
            continue
        seen.add(full)
        publish_date = _extract_date_like_text(str(item.get("publishTime") or ""))
        rows.append({"title": title, "url": full, "publish_date": publish_date})
    return rows


def _safe_jilin_content_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "jleea.com.cn" not in host:
        return None
    path = (p.path or "").lower()
    if not path.startswith("/front/content/"):
        return None
    return url


def _stub_items(note: str) -> list[dict]:
    return [{"title": note, "url": JILIN_ENTRY, "publish_date": ""}]


def _extract_date_like_text(text: str) -> str:
    # publishTime 形如 `YYYY-MM-DD HH:MM:SS`
    import re

    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", text)
    if not m:
        return ""
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

