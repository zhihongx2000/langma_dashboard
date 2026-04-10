from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ContentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    url: str
    publish_date: date | None = None
    crawled_at: datetime


class ContentDetail(ContentListItem):
    content_text: str | None = None
    html_snapshot: str | None = None
    section_id: int
    is_deleted: bool


class ContentPage(BaseModel):
    total: int
    page: int
    page_size: int
    data: list[ContentListItem]

