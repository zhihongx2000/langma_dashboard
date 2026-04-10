from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.content import Content
from app.models.province import Province
from app.models.section import Section
from app.models.update_log import UpdateLog
from app.schemas.province import ProvinceOut, ProvinceStatsOut
from app.utils.time import utc_now

router = APIRouter(prefix="/api/provinces", tags=["provinces"])


@router.get("", response_model=list[ProvinceOut])
def list_provinces(db: Session = Depends(get_db)):
    provinces = db.scalars(select(Province).order_by(Province.id)).all()
    result: list[ProvinceOut] = []
    for province in provinces:
        section_count = db.scalar(select(func.count(Section.id)).where(Section.province_id == province.id)) or 0
        item = ProvinceOut.model_validate(province)
        item.section_count = section_count
        result.append(item)
    return result


@router.get("/{province_id}/stats", response_model=ProvinceStatsOut)
def province_stats(province_id: int, db: Session = Depends(get_db)):
    province = db.get(Province, province_id)
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")

    total_contents = db.scalar(
        select(func.count(Content.id))
        .join(Section, Section.id == Content.section_id)
        .where(Section.province_id == province_id, Content.is_deleted.is_(False))
    ) or 0

    last_update = db.scalar(
        select(func.max(UpdateLog.detected_at))
        .join(Content, Content.id == UpdateLog.content_id)
        .join(Section, Section.id == Content.section_id)
        .where(Section.province_id == province_id)
    )

    today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today_start + timedelta(days=1)
    new_today = db.scalar(
        select(func.count(UpdateLog.id))
        .join(Content, Content.id == UpdateLog.content_id)
        .join(Section, Section.id == Content.section_id)
        .where(
            Section.province_id == province_id,
            UpdateLog.update_type == "new",
            UpdateLog.detected_at >= today_start,
            UpdateLog.detected_at < tomorrow,
        )
    ) or 0

    return ProvinceStatsOut(total_contents=total_contents, last_update=last_update, new_today=new_today)
