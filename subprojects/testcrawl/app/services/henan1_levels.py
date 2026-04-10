"""
河南（1）— 自学考试（固定一级板块）。

入口：`http://www.haeea.cn/zixuekaoshi/`
说明：
- 该站点在服务器侧有较强反爬策略，非浏览器环境常见 `412 Precondition Failed`。
- 本模块先保证固定一级板块可用，并在可抓到列表时返回文章；抓取失败时返回说明条目。
"""

from __future__ import annotations

import subprocess
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

HENAN1_ENTRY = "http://www.haeea.cn/zixuekaoshi/"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("自学考试", HENAN1_ENTRY),
)


def get_henan1_levels() -> dict:
    level1: list[dict] = []
    for name, page_url in LEVEL1_SECTIONS:
        try:
            final_url, html = _fetch_henan_html(page_url, timeout_sec=30)
            soup = BeautifulSoup(html, "lxml")
            items = _parse_henan_links(soup, base_url=final_url)
            if not items:
                items = _stub_items(page_url, "当前未解析到河南自学考试列表（可能为反爬拦截或结构变更）。")
        except Exception:
            items = _stub_items(page_url, "河南站点当前返回 412/拦截，暂无法自动抓取列表。")
        level1.append({"name": name, "items": items})

    return {"source_url": HENAN1_ENTRY, "level1": level1}


def _fetch_henan_html(url: str, *, timeout_sec: int = 30) -> tuple[str, str]:
    # 1) 先尝试 Playwright（可执行反爬 JS 挑战）
    try:
        result = fetch_html(url, timeout_sec=timeout_sec, prefer_browser=True)
        if result.html and "412" not in (result.html[:1200] or ""):
            return result.url, result.html
    except Exception:
        pass

    # 2) requests 会话预热，降低 412 命中概率
    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "keep-alive",
    }
    try:
        session.get("http://www.haeea.cn/", headers=headers, timeout=timeout_sec)
        resp = session.get(
            url,
            headers={**headers, "Referer": "http://www.haeea.cn/"},
            timeout=timeout_sec,
            allow_redirects=True,
        )
        if resp.status_code < 400:
            resp.encoding = resp.apparent_encoding or resp.encoding or "utf-8"
            return resp.url or url, resp.text
    except Exception:
        pass

    # 3) requests 仍失败时回退系统 curl（项目中内蒙古/湖南已验证可行）
    try:
        result = fetch_html(url, timeout_sec=timeout_sec, prefer_browser=False)
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


def _parse_henan_links(soup: BeautifulSoup, *, base_url: str, max_items: int = 80) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = _safe_henan_url(urljoin(base_url, href))
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


def _safe_henan_url(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return None
    host = (p.netloc or "").lower()
    if "haeea.cn" not in host:
        return None
    path = (p.path or "").lower()
    if "/zixuekaoshi/" not in path:
        return None
    return url


def _stub_items(section_url: str, note: str) -> list[dict]:
    return [{"title": note, "url": section_url, "publish_date": ""}]


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

