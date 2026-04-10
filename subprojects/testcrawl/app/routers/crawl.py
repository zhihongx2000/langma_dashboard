from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models.crawl_job import CrawlJob
from app.schemas.crawl import CrawlJobOut, CrawlQueueOut, CrawlTriggerIn
from app.services.crawler import create_job, run_job
from app.services.refresh_report import build_job_report, latest_completed_full_job_id
from app.utils.time import utc_now

router = APIRouter(prefix="/api/crawl", tags=["crawl"])


def _run_job_in_new_session(job_id: int) -> None:
    db = SessionLocal()
    try:
        run_job(db, job_id)
    finally:
        db.close()


# 未做鉴权：仅适合本机/内网；公网部署请用反向代理或恢复 X-API-Key 校验。
@router.post("/trigger", response_model=CrawlJobOut)
def trigger_crawl(payload: CrawlTriggerIn, bg: BackgroundTasks, db: Session = Depends(get_db)):
    if payload.type not in {"full", "province", "section"}:
        raise HTTPException(status_code=400, detail="type must be full|province|section")
    target_id = payload.province_id if payload.type == "province" else payload.section_id
    job = create_job(db, payload.type, target_id=target_id)
    bg.add_task(_run_job_in_new_session, job.id)
    return CrawlJobOut(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        total_tasks=job.total_tasks,
        completed_tasks=job.completed_tasks,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/status/{job_id}", response_model=CrawlJobOut)
def crawl_status(job_id: int, db: Session = Depends(get_db)):
    job = db.get(CrawlJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return CrawlJobOut(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        total_tasks=job.total_tasks,
        completed_tasks=job.completed_tasks,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/queue", response_model=CrawlQueueOut)
def crawl_queue(db: Session = Depends(get_db)):
    pending = db.scalar(select(func.count(CrawlJob.id)).where(CrawlJob.status == "pending")) or 0
    running = db.scalar(select(func.count(CrawlJob.id)).where(CrawlJob.status == "running")) or 0
    today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
    completed_today = db.scalar(
        select(func.count(CrawlJob.id)).where(
            and_(CrawlJob.status == "completed", CrawlJob.completed_at >= today_start)
        )
    ) or 0
    return CrawlQueueOut(pending=pending, running=running, completed_today=completed_today)


@router.get("/report/{job_id}")
def crawl_report(job_id: int, db: Session = Depends(get_db)):
    report = build_job_report(db, job_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return report


@router.get("/report-latest")
def crawl_report_latest(db: Session = Depends(get_db)):
    job_id = latest_completed_full_job_id(db)
    if not job_id:
        return {"job": None, "summary": {"total_updates": 0, "new_count": 0, "modified_count": 0, "deleted_count": 0}, "items": []}
    report = build_job_report(db, job_id)
    return report
