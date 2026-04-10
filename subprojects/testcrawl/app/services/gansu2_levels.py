"""
甘肃省自学考试网上报名系统 public-info（甘肃2，kw.ganseea.cn）一级板块。

站点为 Vue SPA，列表数据多在表格中，无独立文章 URL。使用 Playwright 打开首页并点击侧栏
菜单，从 ``table tbody tr`` 抽取行文本；每条 ``url`` 为该板块入口（含 hash）便于浏览器打开。

部分菜单在非网报开放期仅展示「报考须知」，与 101.md 中「省级课程大纲 / 顶替表」等一致时可能无表格，
此时返回少量说明性条目。

菜单文案（专接本 / 二学历）与官网一致，使用弯引号 U+201C/U+201D。
"""

from __future__ import annotations

import re
import sys
from typing import Literal
from urllib.parse import urljoin

from app.config import get_settings

GANSU2_ENTRY = "https://kw.ganseea.cn/public-info/"

# 显示名（对齐 101.md）、侧栏点击文案（与官网 innerText 一致）、hash、模式
GANSU2_SECTIONS: tuple[tuple[str, str | None, str, Literal["home", "table"]], ...] = (
    ("首页", None, "/", "home"),
    ("开考专业查询", "开考专业查询", "/kkzy", "table"),
    ("社会型专业开考课程", "社会型专业开考课程", "/shxzykkkc", "table"),
    ("应用型专业开考课程", "应用型专业开考课程", "/yyxzykkkc", "table"),
    ("专接本开考课程", "\u201c专接本\u201d开考课程", "/zjbkkkc", "table"),
    ("二年级开考课程", "\u201c二学历\u201d开考课程", "/exlkkkc", "table"),
    ("报名及考试地点联系方式", "报名及考试地点联系方式", "/bmjksdd", "table"),
    ("自考教材信息", "自考教材信息", "/zkjcxx", "table"),
    ("自学考试省级课程大纲", "自学考试省级课程大纲", "/zkjcdg", "table"),
    ("新旧专业课程顶替关系表（社会型）", "新旧专业课程顶替关系表 (社会型)", "/wbczzn", "table"),
    ("新旧专业课程顶替关系表（应用型）", "新旧专业课程顶替关系表 (应用型)", "/wbczzn", "table"),
)

SECTION_OPEN_URLS: dict[str, str] = {
    "自学考试省级课程大纲": "https://www.ganseea.cn/zikaodagang/",
    "新旧专业课程顶替关系表（社会型）": "https://www.ganseea.cn/zixuekaoshi/1766.html",
    "新旧专业课程顶替关系表（应用型）": "https://www.ganseea.cn/zixuekaoshi/1767.html",
}


def get_gansu2_levels() -> dict:
    settings = get_settings()
    level1: list[dict] = []
    # Windows + 当前运行时下 Playwright 容易阻塞，先快速回退，避免 UI 长时间卡住。
    if sys.platform.startswith("win"):
        for name, _, hash_path, _ in GANSU2_SECTIONS:
            section_url = _section_url(hash_path)
            items = [
                {
                    "title": f"点击进入「{name}」官网查询页",
                    "url": section_url,
                    "publish_date": "",
                }
            ]
            open_url = SECTION_OPEN_URLS.get(name)
            if open_url:
                items.append(
                    {
                        "title": f"官方直达入口：{name}",
                        "url": open_url,
                        "publish_date": "",
                    }
                )
            level1.append(
                {
                    "name": name,
                    "items": items,
                }
            )
        return {"source_url": GANSU2_ENTRY, "level1": level1}

    if not settings.crawl_use_browser:
        for name, _, hash_path, _ in GANSU2_SECTIONS:
            level1.append(
                {
                    "name": name,
                    "items": _stub_items(
                        _section_url(hash_path),
                        "当前环境未启用浏览器抓取（crawl_use_browser=false），暂无法解析甘肃2表格。",
                    ),
                }
            )
        return {"source_url": GANSU2_ENTRY, "level1": level1}

    try:
        from playwright.sync_api import Error, TimeoutError as PlaywrightTimeoutError, sync_playwright
    except Exception:
        for name, _, hash_path, _ in GANSU2_SECTIONS:
            level1.append(
                {
                    "name": name,
                    "items": _stub_items(
                        _section_url(hash_path),
                        "当前环境缺少 Playwright 运行能力，暂无法解析甘肃2表格。",
                    ),
                }
            )
        return {"source_url": GANSU2_ENTRY, "level1": level1}

    timeout_ms = min(int(settings.crawl_timeout_sec * 1000), settings.playwright_timeout_ms)
    post_wait = max(settings.playwright_post_load_wait_ms, 500)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=settings.playwright_headless)
            page = browser.new_page()
            page.set_extra_http_headers(
                {
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Cache-Control": "no-cache",
                }
            )
            for display_name, menu_label, hash_path, mode in GANSU2_SECTIONS:
                items = _collect_section(
                    page,
                    display_name=display_name,
                    menu_label=menu_label,
                    hash_path=hash_path,
                    mode=mode,
                    timeout_ms=timeout_ms,
                    post_wait_ms=post_wait,
                    wait_until=settings.playwright_wait_until,
                )
                level1.append({"name": display_name, "items": items})
            browser.close()
    except (PlaywrightTimeoutError, Error, Exception):
        if len(level1) != len(GANSU2_SECTIONS):
            level1 = [
                {
                    "name": n,
                    "items": _stub_items(
                        _section_url(hash_path),
                        "甘肃2 抓取失败（超时或站点结构变化），请稍后重试。",
                    ),
                }
                for n, _, hash_path, _ in GANSU2_SECTIONS
            ]

    return {"source_url": GANSU2_ENTRY, "level1": level1}


def _collect_section(
    page,
    *,
    display_name: str,
    menu_label: str | None,
    hash_path: str,
    mode: Literal["home", "table"],
    timeout_ms: int,
    post_wait_ms: int,
    wait_until: str,
) -> list[dict]:
    section_url = _section_url(hash_path)
    items: list[dict] = []

    page.goto(GANSU2_ENTRY, wait_until=wait_until, timeout=timeout_ms)
    page.wait_for_timeout(post_wait_ms)

    if mode == "home":
        return _parse_home(page, section_url)

    if not menu_label:
        return items

    try:
        page.get_by_text(menu_label, exact=True).first.click(timeout=15000)
    except Exception:
        return _stub_items(section_url, "未能点击侧栏菜单，可能页面结构已变更。")

    page.wait_for_timeout(max(post_wait_ms, 2800))

    rows = page.locator("table tbody tr")
    try:
        rows.first.wait_for(state="attached", timeout=12000)
    except Exception:
        return _empty_or_notice_placeholder(page, section_url, display_name)

    n = rows.count()
    if n == 0:
        return _empty_or_notice_placeholder(page, section_url, display_name)

    seen: set[str] = set()
    for tr in rows.all()[:120]:
        raw = _clean_row(tr.inner_text())
        if not raw or len(raw) < 3:
            continue
        if _is_table_header_row(raw):
            continue
        if raw in seen:
            continue
        seen.add(raw)
        items.append({"title": raw[:400], "url": section_url, "publish_date": ""})
        if len(items) >= 80:
            break

    if not items:
        return _empty_or_notice_placeholder(page, section_url, display_name)
    return items


def _parse_home(page, section_url: str) -> list[dict]:
    items: list[dict] = []
    try:
        t = page.get_by_text("甘肃省高等教育自学考试网上报名报考须知", exact=False).first.inner_text(timeout=5000)
        t = " ".join((t or "").split()).strip()
        if t:
            items.append({"title": t[:200], "url": section_url, "publish_date": ""})
    except Exception:
        pass
    if not items:
        blob = page.evaluate("() => (document.body.innerText||'').slice(0, 400)")
        blob = " ".join(blob.split()).strip()
        if blob:
            items.append({"title": blob[:200], "url": section_url, "publish_date": ""})

    try:
        link = page.locator("a", has_text=re.compile(r"操作手册")).first
        href = link.get_attribute("href")
        if href:
            full = urljoin(GANSU2_ENTRY, href)
            items.append({"title": "网报操作手册（下载）", "url": full, "publish_date": ""})
    except Exception:
        pass

    return items


def _section_url(hash_path: str) -> str:
    path = hash_path.strip() or "/"
    if not path.startswith("/"):
        path = "/" + path
    return f"{GANSU2_ENTRY}#{path}"


def _stub_items(section_url: str, note: str | None = None) -> list[dict]:
    msg = note or "当前页面未展示表格数据（常见原因为未在开放查询期，官网仅显示报考须知）。请稍后在官网同菜单下查看。"
    return [{"title": msg, "url": section_url, "publish_date": ""}]


def _empty_or_notice_placeholder(page, section_url: str, display_name: str) -> list[dict]:
    body = ""
    try:
        body = page.evaluate("() => (document.body.innerText||'')")
    except Exception:
        pass
    if body and "网上报名报考须知" in body:
        return _stub_items(
            section_url,
            f"「{display_name}」当前与首页一致为报考须知，无列表表格。",
        )
    return _stub_items(section_url)


def _clean_row(text: str) -> str:
    return " ".join((text or "").replace("\r", "").split()).strip()


def _is_table_header_row(text: str) -> bool:
    if "专业名称" in text and "上午" in text and "下午" in text:
        return True
    if "课程代码" in text and "教材名称" in text:
        return True
    if "报名点名称" in text and "地址" in text:
        return True
    if "专业代码" in text and "专业名称" in text:
        return True
    return False
