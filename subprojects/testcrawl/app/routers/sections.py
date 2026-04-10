from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.section import Section
from app.schemas.section import SectionOut

router = APIRouter(tags=["sections"])


@router.get("/api/provinces/{province_id}/sections", response_model=list[SectionOut])
def list_sections(province_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(select(Section).where(Section.province_id == province_id).order_by(Section.id)).all()
    return rows


@router.get("/api/sections/{section_id}", response_model=SectionOut)
def get_section(section_id: int, db: Session = Depends(get_db)):
    row = db.get(Section, section_id)
    if not row:
        raise HTTPException(status_code=404, detail="Section not found")
    return row

