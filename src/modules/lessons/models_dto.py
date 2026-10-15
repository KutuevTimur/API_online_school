from datetime import datetime, UTC
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, field_validator

from src.modules.base.orm_dto import ORMDTO
from src.modules.base.url_validation import CallURL
from src.modules.lessons.models import LessonStatus

Duration = Annotated[int, Field(strict=True, gt=0, le=2147483647)]


class LessonDTO(ORMDTO):
    id: int
    course_id: int
    teacher_id: int
    title: str
    topic: str | None = None
    description: str | None = None
    scheduled_at: datetime
    duration_minutes: int = 55
    status: LessonStatus = LessonStatus.SCHEDULED
    call_url_override: str | None = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False
    deleted_at: datetime | None = None


class ScheduleWarning(BaseModel):
    code: str = "teacher_time_overlap"
    lesson_ids: list[int]


class LessonResponseDTO(ORMDTO):
    id: int
    course_id: int
    teacher_user_id: int
    title: str
    topic: str | None = None
    description: str | None = None
    scheduled_at: datetime
    duration_minutes: int = 55
    status: LessonStatus = LessonStatus.SCHEDULED
    call_url_override: str | None = None
    effective_call_url: str | None = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False
    deleted_at: datetime | None = None
    has_lecture: bool = False
    has_homework: bool = False
    # Populated only on the owning teacher's create/update response.
    warnings: list[ScheduleWarning] = Field(default_factory=list)

    @field_validator("scheduled_at")
    @classmethod
    def utc_time(cls, value: datetime) -> datetime:
        try:
            return value.astimezone(UTC)
        except OverflowError as exc:
            raise ValueError("UTC time is outside the supported datetime range") from exc


class CreateLessonRequestDTO(BaseModel):
    course_id: int = Field(gt=0)
    student_user_id: int | None = Field(default=None, gt=0)
    title: str = Field(min_length=1, max_length=1000)
    topic: str | None = None
    description: str | None = None
    scheduled_at: AwareDatetime
    duration_minutes: Duration = 55
    status: LessonStatus = LessonStatus.SCHEDULED
    call_url_override: CallURL | None = None
    model_config = ConfigDict(extra="forbid")

    @field_validator("scheduled_at")
    @classmethod
    def utc_time(cls, value: datetime) -> datetime:
        try:
            return value.astimezone(UTC)
        except OverflowError as exc:
            raise ValueError("UTC time is outside the supported datetime range") from exc


class CreateLessonDTO(BaseModel):
    course_id: int
    teacher_id: int
    title: str
    topic: str | None = None
    description: str | None = None
    scheduled_at: datetime
    duration_minutes: int = 55
    status: LessonStatus = LessonStatus.SCHEDULED
    call_url_override: str | None = None


class UpdateLessonRequestDTO(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=1000)
    topic: str | None = None
    description: str | None = None
    scheduled_at: AwareDatetime | None = None
    duration_minutes: Duration | None = None
    status: LessonStatus | None = None
    call_url_override: CallURL | None = None
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    @field_validator("title", "scheduled_at", "duration_minutes", "status", mode="before")
    @classmethod
    def non_nullable_fields(cls, value: object) -> object:
        if value is None:
            raise ValueError("This field cannot be null")
        return value

    @field_validator("scheduled_at")
    @classmethod
    def utc_time(cls, value: datetime) -> datetime:
        try:
            return value.astimezone(UTC)
        except OverflowError as exc:
            raise ValueError("UTC time is outside the supported datetime range") from exc
