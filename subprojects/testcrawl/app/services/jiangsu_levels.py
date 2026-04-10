"""
江苏省教育考试院 — 自学考试栏目固定一级板块（与官网自学考试导航一致）。
列表页统一使用 `.news-list li` + `a.content-list-ul-a`。
"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

# 与 get.txt 自学考试入口一致
JIANGSU_SELFLEARNING_ROOT = "https://www.jseea.cn/webfile/examination/selflearning/"

# （展示名，列表页绝对 URL）— 政策文件取自自考频道下栏目，不含「研究」大类
# 「考试计划」在官网为子导航，拆成四个一级板块（与自学考试首页侧栏一致）
_PLAN_BASE = "https://www.jseea.cn/webfile/selflearning_plan"
_EXAM_BASE = "https://www.jseea.cn/webfile/selflearning_exam"
_KJGL_BASE = "https://www.jseea.cn/webfile/selflearning_kjgl"
LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("招考信息", "https://www.jseea.cn/webfile/selflearning/selflearning_infomation/"),
    ("政策文件", "https://www.jseea.cn/webfile/selflearning/selflearning_files/"),
    ("自考发展概况", "https://www.jseea.cn/webfile/selflearning/selflearning_zkfzgk/"),
    ("考试计划-专业建设", f"{_PLAN_BASE}/self_learning_zyjs/"),
    ("考试计划-考试日程", f"{_PLAN_BASE}/self_learning_ksrc/"),
    ("考试计划-考试大纲", f"{_PLAN_BASE}/selflearning_jcdg/"),
    ("考试计划-计划简编", f"{_PLAN_BASE}/self_learning_jhja/"),
    # 「考试信息」子导航 → 三个一级板块（展示名加前缀便于 UI 识别）
    ("考试信息-报名", f"{_EXAM_BASE}/selflearning_apply/"),
    ("考试信息-考试", f"{_EXAM_BASE}/selflearning_exam_exam/"),
    ("考试信息-成绩", f"{_EXAM_BASE}/selflearning_check_score/"),
    # 「考籍管理」子导航 → 五个一级板块
    ("考籍管理-实践论文", f"{_KJGL_BASE}/selflearning_sjlw/"),
    ("考籍管理-本科资审", f"{_KJGL_BASE}/selflearning_bkzs/"),
    ("考籍管理-毕业办理", f"{_KJGL_BASE}/selflearning_bybl/"),
    ("考籍管理-转考免考", f"{_KJGL_BASE}/selflearning_zkmk/"),
    ("考籍管理-学士学位", f"{_KJGL_BASE}/selflearning_xsxw/"),
)


def get_jiangsu_levels() -> dict:
    level1: list[dict] = []
    for display_name, list_url in LEVEL1_SECTIONS:
        result = fetch_html(list_url, timeout_sec=25, prefer_browser=False)
        soup = BeautifulSoup(result.html, "lxml")
        items = _parse_news_list(soup, base_url=result.url)
        level1.append({"name": display_name, "items": items})

    return {"source_url": JIANGSU_SELFLEARNING_ROOT, "level1": level1}


def _parse_news_list(soup: BeautifulSoup, *, base_url: str, max_items: int = 80) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for li in soup.select(".news-list li"):
        a = li.select_one("a.content-list-ul-a[href]") or li.find("a", href=True)
        if not a:
            continue
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or "javascript:" in href.lower():
            continue

        full = _normalize_href(href, base_url=base_url)
        if not full or not _safe_jseea_url(full):
            continue

        span = a.find("span")
        publish_date = _clean_text(span.get_text(" ", strip=True)) if span else ""
        if span is not None:
            span.decompose()
        title = _clean_text(a.get_text(" ", strip=True))
        if len(title) < 2:
            continue

        if full in seen:
            continue
        seen.add(full)
        rows.append({"title": title, "url": full, "publish_date": publish_date})
        if len(rows) >= max_items:
            break
    return rows


def _normalize_href(href: str, *, base_url: str) -> str:
    h = href.strip()
    if h.startswith("//"):
        return "https:" + h
    return urljoin(base_url, h)


def _safe_jseea_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None
    host = parsed.netloc.lower()
    if "jseea.cn" not in host:
        return None
    return url


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()
