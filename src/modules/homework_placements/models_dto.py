from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from src.modules.base.orm_dto import ORMDTO


class AddDebtRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lesson_id: int = Field(gt=0)


class DeadlineEventResponseDTO(ORMDTO):
    id: int
    due_lesson_id: int | None
    due_at: datetime | None
    reason: str
    created_at: datetime


class PlacementResponseDTO(BaseModel):
    id: int
    homework_id: int
    lesson_id: int
    kind: str
    due_lesson_id: int | None
    due_at: datetime | None
    created_at: datetime
    frozen: bool
    events: list[DeadlineEventResponseDTO]
