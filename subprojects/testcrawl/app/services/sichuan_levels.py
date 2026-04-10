from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.content_extractor import extract_main_text, extract_xjzk_detail_text
from app.services.fetcher import fetch_html
from app.utils.html_cleaner import normalize_html

SICHUAN_ROOT_URL = "https://www.sceea.cn/Html/ZXKS.html"

LEVEL1_COMPOSITE = "综合信息"
LEVEL1_POLICY = "自考政策"
LEVEL1_HOT = "热门信息"


def get_sichuan_levels() -> dict:
    result = fetch_html(SICHUAN_ROOT_URL, timeout_sec=25, prefer_browser=False)
    soup = BeautifulSoup(result.html, "lxml")

    level_map: dict[str, list[dict]] = {
        LEVEL1_COMPOSITE: [],
        LEVEL1_POLICY: [],
        LEVEL1_HOT: [],
    }

    for panel in soup.select("div.zk-right div.detail"):
        title_node = panel.select_one(".top .title")
        panel_title = _clean_text(title_node.get_text(" ", strip=True) if title_node else "")
        level1_name = None
        if LEVEL1_COMPOSITE in panel_title:
            level1_name = LEVEL1_COMPOSITE
        elif LEVEL1_POLICY in panel_title:
            level1_name = LEVEL1_POLICY
        if not level1_name:
            continue
        level_map[level1_name].extend(_collect_links(panel, base_url=result.url))

    top_news = soup.select("div.top-news ul.list li")
    for li in top_news:
        a = li.select_one("a[href]")
        if not a:
            continue
        title = _clean_text(a.get_text(" ", strip=True))
        href = a.get("href", "").strip()
        if not title or not href:
            continue
        full_url = _safe_sceea_url(urljoin(result.url, href))
        if not full_url:
            continue
        date_node = li.select_one("p")
        publish_date = _clean_text(date_node.get_text(" ", strip=True) if date_node else "")
        level_map[LEVEL1_HOT].append({"title": title, "url": full_url, "publish_date": publish_date})

    payload = []
    for name in [LEVEL1_COMPOSITE, LEVEL1_POLICY, LEVEL1_HOT]:
        seen = set()
        items = []
        for row in level_map[name]:
            if row["url"] in seen:
                continue
            seen.add(row["url"])
            items.append(row)
        payload.append({"name": name, "items": items})

    return {
        "source_url": result.url,
        "level1": payload,
    }


def get_level3_content(url: str) -> dict:
    safe = _safe_http_url(url)
    if not safe:
        return {"ok": False, "error": "invalid url"}
    path = urlparse(safe).path.lower()
    if path.endswith(".pdf"):
        pdf_msg = (
            "该链接直接指向 PDF 文件，无法在此提取文字正文。\n"
            f"请在浏览器中打开下载：{safe}"
        )
        return {
            "ok": True,
            "url": safe,
            "title": path.rsplit("/", 1)[-1] or "PDF",
            "content_text": pdf_msg,
            "content_preview": pdf_msg[:1200],
        }
    result = fetch_html(safe, timeout_sec=25, prefer_browser=False)
    html = normalize_html(result.html)
    soup = BeautifulSoup(html, "lxml")
    title = _extract_title(soup)
    host = urlparse(safe).netloc.lower()
    if "xjzk.gov.cn" in host:
        xj = extract_xjzk_detail_text(html, safe)
        if xj:
            content = xj
        else:
            content = extract_main_text(html, url=safe)
    else:
        content = extract_main_text(html, url=safe)
    return {
        "ok": True,
        "url": safe,
        "title": title,
        "content_text": content,
        "content_preview": content[:1200],
    }


def _collect_links(container, base_url: str) -> list[dict]:
    rows = []
    for li in container.select("ul.list li"):
        a = li.select_one("a[href]")
        if not a:
            continue
        title = _clean_text(a.get_text(" ", strip=True))
        href = a.get("href", "").strip()
        if not title or not href:
            continue
        full_url = _safe_sceea_url(urljoin(base_url, href))
        if not full_url:
            continue
        date_node = li.select_one("p")
        publish_date = _clean_text(date_node.get_text(" ", strip=True) if date_node else "")
        rows.append({"title": title, "url": full_url, "publish_date": publish_date})
    return rows


def _extract_title(soup: BeautifulSoup) -> str:
    for selector in ["h1", "div.title h2", "div.article-title", "title"]:
        node = soup.select_one(selector)
        if node:
            text = _clean_text(node.get_text(" ", strip=True))
            if text:
                return text
    return "未命名内容"


def _safe_http_url(url: str) -> str | None:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None
    return url.strip()


def _safe_sceea_url(url: str) -> str | None:
    u = _safe_http_url(url)
    if not u:
        return None
    if "sceea.cn" not in urlparse(u).netloc.lower():
        return None
    return u


def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()
