from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import verify_admin_api_key
from app.models.content import Content
from app.models.province import Province
from app.models.section import Section
from app.models.update_log import UpdateLog
from app.schemas.common import MessageResponse
from app.schemas.update import UpdateLogOut
from app.utils.time import utc_now

router = APIRouter(prefix="/api/updates", tags=["updates"])


@router.get("", response_model=list[UpdateLogOut])
def list_updates(
    unread_only: bool = Query(default=True),
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(UpdateLog)
    if unread_only:
        stmt = stmt.where(UpdateLog.is_read.is_(False))
    rows = db.scalars(stmt.order_by(UpdateLog.detected_at.desc()).limit(limit)).all()
    return [
        UpdateLogOut(
            id=row.id,
            content_id=row.content_id,
            update_type=row.update_type,
            detected_at=row.detected_at,
            is_read=row.is_read,
        )
        for row in rows
    ]


@router.put("/{update_id}/read", response_model=MessageResponse, dependencies=[Depends(verify_admin_api_key)])
def mark_read(update_id: int, db: Session = Depends(get_db)):
    row = db.get(UpdateLog, update_id)
    if row:
        row.is_read = True
        db.commit()
    return MessageResponse(message="ok")


@router.put("/read-all", response_model=MessageResponse, dependencies=[Depends(verify_admin_api_key)])
def mark_all_read(db: Session = Depends(get_db)):
    db.execute(update(UpdateLog).values(is_read=True))
    db.commit()
    return MessageResponse(message="ok")


@router.get("/province-week")
def list_province_week_updates(
    province_id: int = Query(..., ge=1),
    days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=80, ge=1, le=300),
    db: Session = Depends(get_db),
):
    since = utc_now() - timedelta(days=days)
    stmt = (
        select(UpdateLog, Content, Section, Province)
        .join(Content, Content.id == UpdateLog.content_id)
        .join(Section, Section.id == Content.section_id)
        .join(Province, Province.id == Section.province_id)
        .where(Province.id == province_id, UpdateLog.detected_at >= since)
        .order_by(UpdateLog.detected_at.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    province_name = rows[0][3].name if rows else ""
    items = [
        {
            "update_id": ul.id,
            "type": ul.update_type,
            "detected_at": ul.detected_at,
            "title": content.title,
            "url": content.url,
            "section": section.name,
            "province": province.name,
        }
        for ul, content, section, province in rows
    ]
    summary = {
        "total_updates": len(items),
        "new_count": sum(1 for i in items if i["type"] == "new"),
        "modified_count": sum(1 for i in items if i["type"] == "modified"),
        "deleted_count": sum(1 for i in items if i["type"] == "deleted"),
    }
    return {
        "province_id": province_id,
        "province_name": province_name,
        "days": days,
        "summary": summary,
        "items": items,
    }

