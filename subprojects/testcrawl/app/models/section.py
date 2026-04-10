from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    province_id: Mapped[int] = mapped_column(ForeignKey("provinces.id"), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("sections.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    url: Mapped[str] = mapped_column(String(1000), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    is_auto_discovered: Mapped[bool] = mapped_column(default=False)
    content_count: Mapped[int] = mapped_column(default=0)
    last_crawl_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )

    province = relationship("Province", back_populates="sections")
    contents = relationship("Content", back_populates="section", cascade="all, delete-orphan")
