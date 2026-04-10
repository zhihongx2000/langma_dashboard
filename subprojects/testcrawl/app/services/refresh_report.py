from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.content import Content
from app.models.crawl_job import CrawlJob
from app.models.province import Province
from app.models.section import Section
from app.models.update_log import UpdateLog


def build_job_report(db: Session, job_id: int) -> dict | None:
    job = db.get(CrawlJob, job_id)
    if not job:
        return None

    if not job.started_at:
        updates = []
    else:
        stmt = (
            select(UpdateLog, Content, Section, Province)
            .join(Content, Content.id == UpdateLog.content_id)
            .join(Section, Section.id == Content.section_id)
            .join(Province, Province.id == Section.province_id)
            .where(UpdateLog.detected_at >= job.started_at)
        )
        if job.completed_at:
            stmt = stmt.where(UpdateLog.detected_at <= job.completed_at)
        updates = db.execute(stmt.order_by(UpdateLog.detected_at.desc()).limit(500)).all()

    items = [
        {
            "update_id": ul.id,
            "type": ul.update_type,
            "detected_at": ul.detected_at,
            "content_id": content.id,
            "title": content.title,
            "url": content.url,
            "section": section.name,
            "province": province.name,
        }
        for ul, content, section, province in updates
    ]
    return {
        "job": {
            "id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        },
        "summary": {
            "total_updates": len(items),
            "new_count": sum(1 for i in items if i["type"] == "new"),
            "modified_count": sum(1 for i in items if i["type"] == "modified"),
            "deleted_count": sum(1 for i in items if i["type"] == "deleted"),
        },
        "items": items,
    }


def latest_completed_full_job_id(db: Session) -> int | None:
    return db.scalar(
        select(CrawlJob.id)
        .where(and_(CrawlJob.job_type == "full", CrawlJob.status == "completed"))
        .order_by(CrawlJob.completed_at.desc().nullslast(), CrawlJob.id.desc())
        .limit(1)
    )
