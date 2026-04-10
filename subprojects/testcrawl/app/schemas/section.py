from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    province_id: int
    parent_id: int | None = None
    name: str
    url: str
    is_auto_discovered: bool
    content_count: int
    last_crawl_at: datetime | None = None

