from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, SessionLocal, engine, get_db
from app.models.content import Content
from app.models.crawl_job import CrawlJob
from app.models.province import Province
from app.routers.contents import router as contents_router
from app.routers.crawl import router as crawl_router
from app.routers.debug import router as debug_router
from app.routers.provinces import router as provinces_router
from app.routers.sections import router as sections_router
from app.routers.test_local import router as test_local_router
from app.routers.updates import router as updates_router
from app.services.seed_loader import make_code, parse_seed_file
from app.services.scheduler import start_scheduler, stop_scheduler
from app.utils.time import utc_now

settings = get_settings()


def bootstrap_provinces_if_empty(db: Session) -> None:
    has_data = db.scalar(select(func.count(Province.id))) or 0
    if has_data > 0:
        return

    seed_path = Path(__file__).resolve().parent.parent / "get.txt"
    items = parse_seed_file(str(seed_path))
    for idx, (name, url) in enumerate(items, start=1):
        code = make_code(name, idx)
        exists = db.scalar(select(Province.id).where(Province.url == url))
        if exists:
            continue
        db.add(Province(code=f"{code}-{idx}", name=name[:90], url=url, status="active"))
    db.commit()


def apply_seed_corrections(db: Session) -> None:
    """
    幂等：与当前 get.txt 对齐已有库。
    - 移除新疆第二入口（jyt 成绩列表）；删除曾命名为「新疆2」的占位省。
    - 甘肃第二条由 old 须知页改为 kw.ganseea.cn 报名 public-info。
    - 「新疆1」改名为「新疆」。
    - 移除海南第二入口（zk.hnks.gov.cn）；删除「海南2」；「海南1」改名为「海南」。
    """
    for url in ("http://jyt.xinjiang.gov.cn/edu/zkcj/list_cx.shtml",):
        row = db.scalar(select(Province).where(Province.url == url))
        if row is not None:
            db.delete(row)

    for row in db.scalars(select(Province).where(Province.name == "新疆2")).all():
        db.delete(row)

    old_g2 = "https://www.ganseea.cn/fuwuzhinan/145.html"
    new_g2 = "https://kw.ganseea.cn/public-info/"
    row = db.scalar(select(Province).where(Province.url == old_g2))
    if row is not None:
        row.url = new_g2

    for row in db.scalars(select(Province).where(Province.name == "新疆1")).all():
        row.name = "新疆"

    for url in (
        "https://zk.hnks.gov.cn/student/ksinfo",
        "https://zk.hnks.gov.cn/student/ksinfo/",
        "http://zk.hnks.gov.cn/student/ksinfo",
        "http://zk.hnks.gov.cn/student/ksinfo/",
    ):
        row = db.scalar(select(Province).where(Province.url == url))
        if row is not None:
            db.delete(row)

    for row in db.scalars(select(Province).where(Province.name == "海南2")).all():
        db.delete(row)

    for row in db.scalars(select(Province).where(Province.name == "海南1")).all():
        row.name = "海南"

    # 重庆入口统一为自学考试栏目页；移除旧入口，避免重复省份。
    cq_new = "https://www.cqksy.cn/web/column/col1846543.html"
    for url in (
        "http://zk.cqksy.cn/zkPage/index#",
        "http://zk.cqksy.cn/zkPage/index",
        "https://zk.cqksy.cn/zkPage/index#",
        "https://zk.cqksy.cn/zkPage/index",
        "http://cqksy.cn/site/default.html",
        "https://cqksy.cn/site/default.html",
    ):
        row = db.scalar(select(Province).where(Province.url == url))
        if row is not None:
            row.url = cq_new

    # 安徽入口统一为自考频道根地址
    ah_new = "https://www.ahzsks.cn/gdjyzxks/"
    for url in (
        "https://www.ahzsks.cn/gdjyzxks/search2.jsp?c=77",
        "http://www.ahzsks.cn/gdjyzxks/search2.jsp?c=77",
    ):
        row = db.scalar(select(Province).where(Province.url == url))
        if row is not None:
            row.url = ah_new

    nm2_new = "https://www.nm.zsks.cn/kszs/zxks/zkxxggl/"
    for url in (
        "https://www.nm.zsks.cn/kszs/zxks/wsbmbkxt_zx/",
        "http://www.nm.zsks.cn/kszs/zxks/wsbmbkxt_zx/",
    ):
        row = db.scalar(select(Province).where(Province.url == url))
        if row is not None:
            row.url = nm2_new

    db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        bootstrap_provinces_if_empty(db)
        apply_seed_corrections(db)
        start_scheduler()
        yield
    finally:
        stop_scheduler()
        db.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)


def create_app() -> FastAPI:
    return app


@app.get("/health")
def health(db: Session = Depends(get_db)):
    running_jobs = db.scalar(select(func.count(CrawlJob.id)).where(CrawlJob.status == "running")) or 0
    last_crawl = db.scalar(select(func.max(Content.crawled_at)))
    queued = db.scalar(select(func.count(CrawlJob.id)).where(CrawlJob.status == "pending")) or 0
    return {
        "status": "healthy",
        "database": "connected",
        "crawler": "running" if running_jobs else "idle",
        "last_crawl": last_crawl,
        "queued_jobs": queued,
        "server_time": utc_now(),
    }


@app.get("/")
def home():
    ui_path = Path(__file__).resolve().parent.parent / "ui" / "index.html"
    return FileResponse(ui_path)


@app.get("/test-ui")
def test_ui():
    ui_path = Path(__file__).resolve().parent.parent / "ui" / "test_ui.html"
    return FileResponse(ui_path)


app.include_router(provinces_router)
app.include_router(sections_router)
app.include_router(contents_router)
app.include_router(crawl_router)
app.include_router(updates_router)
app.include_router(debug_router)
app.include_router(test_local_router)
