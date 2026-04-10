"""
内蒙古（门户1）— nm.zsks.cn 自学考试主站：固定一级「公告栏」「政策规定」。

对应 get.txt 第一条：https://www.nm.zsks.cn/kszs/zxks/
与 zkxxggl 门户（内蒙古2）区分。
"""

from __future__ import annotations

import re
import subprocess
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

NEIMENGGU1_ENTRY = "https://www.nm.zsks.cn/kszs/zxks/"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("公告栏", "https://www.nm.zsks.cn/kszs/zxks/ggl/"),
    ("政策规定", "https://www.nm.zsks.cn/kszs/zxks/zcfg/"),
)

_ARTICLE_SUFFIX = re.compile(r"/t(20\d{6})_\d+\.html?$", re.I)


def get_neimenggu1_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        try:
            final_url, html = _fetch_nm_html(page_url, timeout_sec=25)
            soup = BeautifulSoup(html, "lxml")
            items = _parse_neimenggu1_list(soup, base_url=final_url)
        except Exception:
            items = _stub_items(
                f"「{display_name}」栏目当前访问失败（SSL/网络限制），请稍后重试或直接访问官网。"
            )
            level1.append({"name": display_name, "items": items})
            continue
        if not items:
            items = _stub_items(f"当前未解析到内蒙古自学考试「{display_name}」列表。")
        level1.append({"name": display_name, "items": items})
    return {"source_url": NEIMENGGU1_ENTRY, "level1": level1}


def _parse_neimenggu1_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_neimenggu1_article_url(urljoin(base_url, href))
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
        rows.append(
            {
                "title": title,
                "url": full,
                "publish_date": _date_from_article_url(full) or _extract_date_like(li_text) or _extract_date_like(title),
            }
        )
        if len(rows) >= max_items:
            break
    return rows


def _fetch_nm_html(url: str, *, timeout_sec: int = 25) -> tuple[str, str]:
    """
    nm.zsks.cn 在部分 OpenSSL 环境下会触发 legacy renegotiation 错误。
    先走 requests；失败时回退到系统 curl 以获取真实 HTML。
    """
    try:
        result = fetch_html(url, timeout_sec=timeout_sec, prefer_browser=True)
        return result.url, result.html
    except Exception:
        return url, _fetch_with_curl(url, timeout_sec=timeout_sec)


def _fetch_with_curl(url: str, *, timeout_sec: int = 25) -> str:
    cmd = ["curl.exe", "-L", url, "--max-time", str(timeout_sec)]
    proc = subprocess.run(cmd, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed: code={proc.returncode}")
    return proc.stdout.decode("utf-8", errors="replace")


def _safe_neimenggu1_article_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "nm.zsks.cn" not in host:
        return None
    path = (p.path or "").lower()
    if "/kszs/zxks/" not in path:
        return None
    if "wsbmbkxt" in path:
        return None
    if path.endswith("/index.html"):
        return None
    if not _ARTICLE_SUFFIX.search(path.split("?")[0]):
        return None
    return url


def _date_from_article_url(url: str) -> str:
    m = _ARTICLE_SUFFIX.search((urlparse(url).path or "").lower())
    if not m:
        return ""
    d = m.group(1)
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}"


def _extract_date_like(text: str) -> str:
    m = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", text or "")
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return ""


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _stub_items(message: str) -> list[dict]:
    return [{"title": message, "url": NEIMENGGU1_ENTRY, "publish_date": ""}]
