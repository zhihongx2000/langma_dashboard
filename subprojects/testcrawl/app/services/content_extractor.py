from urllib.parse import urljoin

from bs4 import BeautifulSoup


def extract_main_text(html: str, url: str | None = None) -> str:
    try:
        import trafilatura

        text = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )
        if text and len(text.strip()) > 80:
            return text.strip()
    except Exception:
        pass

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    return text[:30000]


def extract_xjzk_detail_text(html: str, page_url: str) -> str | None:
    """
    新疆考试院文章页：正文在 #detail_conts，避免把全站导航、页脚抓进预览。
    若正文仅为 PDF 附件，则输出简短说明与链接，而不是整页噪声。
    """
    soup = BeautifulSoup(html, "lxml")
    detail = soup.select_one("#detail_conts")
    if not detail:
        return None

    for tag in detail(["script", "style", "noscript"]):
        tag.decompose()

    for nav in detail.select("div.tabPanel, p.ttl"):
        nav.decompose()

    h1 = detail.find("h1")
    title = " ".join((h1.get_text(" ", strip=True) if h1 else "").split()).strip()

    date_el = detail.select_one("div.date")
    pub = " ".join((date_el.get_text(" ", strip=True) if date_el else "").split()).strip()

    txt_el = detail.select_one("div.txt")
    if not txt_el:
        block = "\n".join(x for x in (title, pub) if x)
        return block if block else None

    pdf_blocks: list[str] = []
    for a in list(txt_el.find_all("a", href=True)):
        href = (a.get("href") or "").strip()
        if not href:
            continue
        path_low = href.split("?", 1)[0].lower()
        if path_low.endswith(".pdf"):
            full = urljoin(page_url, href)
            label = " ".join(a.get_text(" ", strip=True).split()).strip() or "PDF"
            pdf_blocks.append(f"{label}\n{full}")
            a.decompose()

    body = " ".join(txt_el.get_text(" ", strip=True).split()).strip()
    lines: list[str] = []
    if title:
        lines.append(title)
    if pub:
        lines.append(pub)
    if body:
        lines.append("")
        lines.append(body)
    if pdf_blocks:
        lines.append("")
        lines.append("【PDF 附件】（请在浏览器中打开下载）")
        lines.extend(pdf_blocks)

    out = "\n".join(lines).strip()
    return out or None

