from datetime import datetime
from typing import Literal
from pydantic import BaseModel
from src.modules.base.orm_dto import ORMDTO


class NotificationResponseDTO(ORMDTO):
    id: int
    event_type: str
    object_type: str
    object_id: int
    created_at: datetime
    read_at: datetime | None


class UnreadCountDTO(BaseModel):
    unread: int


class NotificationTargetDTO(BaseModel):
    available: bool
    message: str | None = None
    object_type: Literal["lesson", "homework", "submission"] | None = None
    object_id: int | None = None
    homework_id: int | None = None
