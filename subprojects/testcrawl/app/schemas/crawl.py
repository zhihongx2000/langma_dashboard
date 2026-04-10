from datetime import datetime

from pydantic import BaseModel, Field


class CrawlTriggerIn(BaseModel):
    type: str = Field(description="full|province|section")
    province_id: int | None = None
    section_id: int | None = None


class CrawlJobOut(BaseModel):
    id: int
    job_type: str
    status: str
    total_tasks: int
    completed_tasks: int
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class CrawlQueueOut(BaseModel):
    pending: int
    running: int
    completed_today: int

