from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProvinceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    url: str
    status: str
    last_crawl_at: datetime | None = None
    section_count: int = 0


class ProvinceStatsOut(BaseModel):
    total_contents: int
    last_update: datetime | None = None
    new_today: int

