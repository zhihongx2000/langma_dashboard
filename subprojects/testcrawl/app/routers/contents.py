from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.content import Content
from app.models.section import Section
from app.schemas.content import ContentDetail, ContentListItem, ContentPage
from app.services.ai_search import search_contents_ai

router = APIRouter(tags=["contents"])


@router.get("/api/sections/{section_id}/contents", response_model=ContentPage)
def list_contents(
    section_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.scalar(
        select(func.count(Content.id)).where(Content.section_id == section_id, Content.is_deleted.is_(False))
    ) or 0
    offset = (page - 1) * page_size
    rows = db.scalars(
        select(Content)
        .where(Content.section_id == section_id, Content.is_deleted.is_(False))
        .order_by(Content.publish_date.desc().nullslast(), Content.crawled_at.desc())
        .offset(offset)
        .limit(page_size)
    ).all()
    return ContentPage(
        total=total,
        page=page,
        page_size=page_size,
        data=[ContentListItem.model_validate(row) for row in rows],
    )


@router.get("/api/contents/{content_id}", response_model=ContentDetail)
def get_content(content_id: int, db: Session = Depends(get_db)):
    row = db.get(Content, content_id)
    if not row:
        raise HTTPException(status_code=404, detail="Content not found")
    return ContentDetail.model_validate(row)


@router.get("/api/contents/search", response_model=list[ContentListItem])
def search_contents(
    keyword: str = Query(min_length=1),
    province_id: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Content).where(
        Content.is_deleted.is_(False),
        or_(Content.title.contains(keyword), Content.content_text.contains(keyword)),
    )
    if province_id is not None:
        stmt = stmt.join(Section, Section.id == Content.section_id).where(Section.province_id == province_id)
    rows = db.scalars(stmt.order_by(Content.crawled_at.desc()).limit(limit)).all()
    return [ContentListItem.model_validate(row) for row in rows]


@router.get("/api/search/ai")
def search_contents_by_ai(
    query: str = Query(min_length=1),
    province_id: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return search_contents_ai(db=db, query=query, province_id=province_id, limit=limit)
