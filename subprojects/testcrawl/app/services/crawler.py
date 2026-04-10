import time
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from urllib.parse import parse_qsl, urlencode, urlunparse

from bs4 import BeautifulSoup
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.content import Content
from app.models.crawl_job import CrawlJob
from app.models.province import Province
from app.models.section import Section
from app.models.update_log import UpdateLog
from app.services.content_extractor import extract_main_text
from app.services.fetcher import fetch_html
from app.services.section_discovery import discover_sections
from app.utils.hash import sha256_text
from app.utils.html_cleaner import normalize_html
from app.utils.time import utc_now

settings = get_settings()
BAD_ARTICLE_SUFFIXES = (".jpg", ".jpeg", ".png", ".gif", ".pdf", ".zip", ".rar")
NOISE_TITLE_KEYWORDS = ("首页", "下一页", "上一页", "更多", "详情", "登录", "注册")
TRACKING_QUERY_KEYS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "spm"}
CHONGQING_ZXKS_ENTRY = "https://www.cqksy.cn/web/column/col1846543.html"
CHONGQING_ZK_SYSTEM_URL = "https://zk.cqksy.cn/zkPage/index#"


def create_job(db: Session, job_type: str, target_id: int | None = None) -> CrawlJob:
    job = CrawlJob(job_type=job_type, target_id=target_id, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def run_job(db: Session, job_id: int) -> None:
    job = db.get(CrawlJob, job_id)
    if not job:
        return

    job.status = "running"
    job.started_at = utc_now()
    job.heartbeat_at = utc_now()
    db.commit()

    try:
        if job.job_type == "full":
            provinces = db.scalars(select(Province).where(Province.status == "active")).all()
            job.total_tasks = len(provinces)
            db.commit()
            for province in provinces:
                crawl_province(db, province, job)
                job.completed_tasks += 1
                job.heartbeat_at = utc_now()
                db.commit()
        elif job.job_type == "province" and job.target_id:
            province = db.get(Province, job.target_id)
            if province:
                job.total_tasks = 1
                db.commit()
                crawl_province(db, province, job)
                job.completed_tasks = 1
                db.commit()
        elif job.job_type == "section" and job.target_id:
            section = db.get(Section, job.target_id)
            if section:
                job.total_tasks = 1
                db.commit()
                crawl_section(db, section)
                job.completed_tasks = 1
                db.commit()
        job.status = "completed"
        job.completed_at = utc_now()
    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = utc_now()
    db.commit()


def crawl_province(db: Session, province: Province, job: CrawlJob | None = None) -> None:
    sections = db.scalars(select(Section).where(Section.province_id == province.id).order_by(Section.id)).all()
    if not sections:
        section_items = discover_sections(province.url, timeout=settings.crawl_timeout_sec)
        for name, url in section_items[: settings.crawl_max_sections_per_province]:
            section = Section(
                province_id=province.id,
                name=name[:180],
                url=url,
                is_auto_discovered=True,
            )
            db.add(section)
        db.commit()
        sections = db.scalars(select(Section).where(Section.province_id == province.id).order_by(Section.id)).all()

    for section in sections[: settings.crawl_max_sections_per_province]:
        crawl_section(db, section)
        if job:
            job.heartbeat_at = utc_now()
            db.commit()
        time.sleep(settings.crawl_request_delay_sec)

    province.last_crawl_at = utc_now()
    province.status = "active"
    db.commit()


def crawl_section(db: Session, section: Section) -> None:
    try:
        result = fetch_html(section.url, timeout_sec=settings.crawl_timeout_sec, prefer_browser=True)
    except Exception:
        section.status = "error"
        section.last_crawl_at = utc_now()
        db.commit()
        return

    soup = BeautifulSoup(result.html, "lxml")
    base_netloc = urlparse(result.url).netloc or urlparse(section.url).netloc
    links: list[tuple[str, str]] = []
    for anchor in soup.select("a[href]"):
        title = _clean_title(anchor.get_text(" ", strip=True))
        href = anchor.get("href", "").strip()
        if not href or href.startswith("javascript:") or len(title) < 4:
            continue
        if _is_noise_title(title):
            continue
        url = _canonicalize_url(urljoin(result.url, href))
        if urlparse(url).netloc != base_netloc:
            continue
        if url.lower().endswith(BAD_ARTICLE_SUFFIXES):
            continue
        links.append((title[:400], url))

    dedup: dict[str, str] = {}
    for title, url in links:
        if url not in dedup:
            dedup[url] = title
        if len(dedup) >= settings.crawl_max_articles_per_section:
            break

    if _is_chongqing_zxks_section(section.url):
        dedup.setdefault(CHONGQING_ZK_SYSTEM_URL, "自考信息管理系统")

    for url, title in dedup.items():
        upsert_article(db, section, title, url)

    section.content_count = db.scalar(
        select(func.count(Content.id)).where(Content.section_id == section.id, Content.is_deleted.is_(False))
    ) or 0
    section.last_crawl_at = utc_now()
    section.status = "active"
    db.commit()


def upsert_article(db: Session, section: Section, title: str, url: str) -> None:
    try:
        result = fetch_html(url, timeout_sec=settings.crawl_timeout_sec, prefer_browser=True)
    except Exception:
        return

    clean_title = _clean_title(title)
    clean_url = _canonicalize_url(url)
    html = normalize_html(result.html)
    body = extract_main_text(html, url=url)
    if len(body) < 20:
        return
    publish_date = _extract_publish_date(clean_title, body)

    content_hash = sha256_text(f"{clean_title}\n{body}")
    existing = db.scalar(select(Content).where(Content.section_id == section.id, Content.url == clean_url).limit(1))

    if existing is None:
        item = Content(
            section_id=section.id,
            title=clean_title,
            url=clean_url,
            publish_date=publish_date,
            content_text=body,
            html_snapshot=html[:100000],
            content_hash=content_hash,
            crawled_at=utc_now(),
        )
        db.add(item)
        db.flush()
        db.add(UpdateLog(content_id=item.id, update_type="new", old_hash=None, new_hash=content_hash))
    elif existing.content_hash != content_hash:
        old_hash = existing.content_hash
        existing.title = clean_title
        existing.url = clean_url
        existing.publish_date = publish_date or existing.publish_date
        existing.content_text = body
        existing.html_snapshot = html[:100000]
        existing.content_hash = content_hash
        existing.crawled_at = utc_now()
        db.add(
            UpdateLog(
                content_id=existing.id,
                update_type="modified",
                old_hash=old_hash,
                new_hash=content_hash,
            )
        )

    db.commit()


def _clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", (title or "")).strip()


def _is_noise_title(title: str) -> bool:
    return any(k in title for k in NOISE_TITLE_KEYWORDS)


def _canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    query_items = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() not in TRACKING_QUERY_KEYS]
    query = urlencode(query_items, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, query, ""))


def _extract_publish_date(title: str, body: str):
    text = f"{title}\n{body[:1200]}"
    patterns = [
        r"(?P<y>20\d{2})[-/.年](?P<m>\d{1,2})[-/.月](?P<d>\d{1,2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        try:
            y = int(match.group("y"))
            m = int(match.group("m"))
            d = int(match.group("d"))
            return datetime(y, m, d).date()
        except Exception:
            continue
    return None


def _is_chongqing_zxks_section(url: str) -> bool:
    return (url or "").rstrip("/").lower() == CHONGQING_ZXKS_ENTRY.rstrip("/").lower()
