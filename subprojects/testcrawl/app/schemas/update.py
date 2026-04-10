from datetime import datetime

from pydantic import BaseModel


class UpdateLogOut(BaseModel):
    id: int
    content_id: int
    update_type: str
    detected_at: datetime
    is_read: bool

