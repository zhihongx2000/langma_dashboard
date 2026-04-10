from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now


class Content(Base):
    __tablename__ = "contents"
    __table_args__ = (UniqueConstraint("section_id", "url", name="uk_section_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), index=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    url: Mapped[str] = mapped_column(String(1000), index=True)
    publish_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    html_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )

    section = relationship("Section", back_populates="contents")
    updates = relationship("UpdateLog", back_populates="content", cascade="all, delete-orphan")
