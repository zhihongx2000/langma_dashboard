from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models.crawl_job import CrawlJob
from app.services.crawler import create_job, run_job

settings = get_settings()
_scheduler: BackgroundScheduler | None = None
_lock = Lock()


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return
    _scheduler = BackgroundScheduler(timezone=settings.auto_refresh_timezone)
    if settings.auto_refresh_enabled:
        _scheduler.add_job(
            _scheduled_full_refresh,
            CronTrigger(hour=settings.auto_refresh_hour, minute=settings.auto_refresh_minute),
            id="daily_full_refresh",
            replace_existing=True,
        )
    _scheduler.start()


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def _scheduled_full_refresh() -> None:
    with _lock:
        db = SessionLocal()
        try:
            running_full = db.scalar(
                select(CrawlJob.id).where(CrawlJob.job_type == "full", CrawlJob.status == "running").limit(1)
            )
            if running_full:
                return
            job = create_job(db, "full")
            run_job(db, job.id)
        finally:
            db.close()

