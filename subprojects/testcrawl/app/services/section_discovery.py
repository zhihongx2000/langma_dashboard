from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.config import get_settings
from app.services.browser_use_adapter import discover_sections_with_browser_use
from app.services.fetcher import fetch_html

settings = get_settings()
CHONGQING_ZXKS_ENTRY = "https://www.cqksy.cn/web/column/col1846543.html"

PRIORITY_KEYWORDS = [
    "通知",
    "公告",
    "报名",
    "报考",
    "成绩",
    "考试",
    "招生",
    "政策",
    "自考",
    "最新",
]

EXCLUDE_KEYWORDS = ["联系我们", "隐私", "登录", "注册", "首页", "网站地图"]
BAD_SUFFIXES = (".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")
PRIORITY_URL_HINTS = ("news", "notice", "policy", "exam", "score", "signup", "zixue", "zk")


def calculate_relevance_score(text: str, url: str) -> float:
    label = f"{text} {url}".lower()
    if any(keyword in label for keyword in EXCLUDE_KEYWORDS):
        return 0.0
    lower_url = url.lower()
    if lower_url.endswith(BAD_SUFFIXES):
        return 0.0

    score = 0.2
    for keyword in PRIORITY_KEYWORDS:
        if keyword in text or keyword in url:
            score += 0.15
    if any(hint in lower_url for hint in PRIORITY_URL_HINTS):
        score += 0.15
    if any(host in url for host in ["edu.cn", "gov.cn"]):
        score += 0.15
    return min(score, 1.0)


def discover_sections(home_url: str, timeout: int = 20, limit: int = 20) -> list[tuple[str, str]]:
    report = discover_sections_with_report(home_url, timeout=timeout, limit=limit)
    return report["merged_results"]


def discover_sections_with_report(home_url: str, timeout: int = 20, limit: int = 20) -> dict:
    if home_url.rstrip("/").lower() == CHONGQING_ZXKS_ENTRY.rstrip("/").lower():
        fixed = [("自学考试", CHONGQING_ZXKS_ENTRY)]
        return {
            "home_url": home_url,
            "fetch_source": "fixed",
            "used_ai": False,
            "static_results": fixed,
            "ai_results": [],
            "merged_results": fixed,
        }

    fetch_source = None
    try:
        result = fetch_html(home_url, timeout_sec=timeout, prefer_browser=True)
        fetch_source = getattr(result, "source", None)
    except Exception:
        result = None

    static_results = _discover_sections_from_html(
        home_url=home_url,
        base_url=result.url if result else home_url,
        html=result.html if result else "",
        limit=limit,
    )
    should_use_ai = len(static_results) < min(limit, settings.browser_use_min_results_trigger)
    ai_results = discover_sections_with_browser_use(home_url) if should_use_ai else []
    merged = _merge_results(static_results, ai_results, limit)
    return {
        "home_url": home_url,
        "fetch_source": fetch_source,
        "used_ai": should_use_ai,
        "static_results": static_results[:limit],
        "ai_results": ai_results[:limit],
        "merged_results": merged[:limit],
    }


def _discover_sections_from_html(home_url: str, base_url: str, html: str, limit: int) -> list[tuple[str, str]]:
    if not html:
        return []

    base_netloc = urlparse(base_url).netloc or urlparse(home_url).netloc
    soup = BeautifulSoup(html, "lxml")
    candidates: list[tuple[str, str, float]] = []
    for anchor in soup.select("a[href]"):
        text = anchor.get_text(" ", strip=True)[:80]
        href = anchor.get("href", "").strip()
        if not href or href.startswith("javascript:"):
            continue
        url = urljoin(base_url, href)
        if urlparse(url).netloc != base_netloc:
            continue
        score = calculate_relevance_score(text, url)
        if score >= 0.3:
            candidates.append((text or "未命名板块", url, score))

    candidates.sort(key=lambda row: row[2], reverse=True)
    dedup: dict[str, tuple[str, str]] = {}
    for name, url, _ in candidates:
        if url not in dedup:
            dedup[url] = (name, url)
        if len(dedup) >= limit:
            break
    return list(dedup.values())


def _merge_results(primary: list[tuple[str, str]], secondary: list[tuple[str, str]], limit: int) -> list[tuple[str, str]]:
    merged: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name, url in primary + secondary:
        if url in seen:
            continue
        seen.add(url)
        merged.append((name, url))
        if len(merged) >= limit:
            break
    return merged
