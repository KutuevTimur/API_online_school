from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from src.modules.base.orm_dto import ORMDTO


class LessonDTO(ORMDTO):
    id: int
    course_id: int
    teacher_id: int

    title: str
    topic: Optional[str] = None
    description: Optional[str] = None

    scheduled_at: datetime
    duration_minutes: Optional[int] = None

    created_at: datetime
    updated_at: datetime


class LessonResponseDTO(ORMDTO):
    id: int
    course_id: int
    teacher_user_id: int

    title: str
    topic: Optional[str] = None
    description: Optional[str] = None

    scheduled_at: datetime
    duration_minutes: Optional[int] = None

    created_at: datetime
    updated_at: datetime


class CreateLessonDTO(BaseModel):
    id: int
    course_id: int
    teacher_id: int

    title: str
    topic: Optional[str] = None
    description: Optional[str] = None

    scheduled_at: datetime
    duration_minutes: Optional[int] = None


class UpdateStudentDTO(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None
    description: Optional[str] = None

    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)