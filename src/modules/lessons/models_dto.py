from src.modules.check_permission.models_dto import AccessContextDTO
from datetime import datetime, UTC
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, field_validator, AliasChoices

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


class RecipientMaterialStatusDTO(BaseModel):
    has_homework: bool
    has_lecture: bool
    homework_not_needed: bool
    lecture_not_needed: bool
    student_user_id: int
    needs_homework: bool
    needs_lecture: bool


class LessonStudentLabelDTO(BaseModel):
    user_id: int
    display_name: str


class LessonResponseDTO(ORMDTO, AccessContextDTO):
    recipient_materials: list[RecipientMaterialStatusDTO] = Field(default_factory=list)
    course_name: str | None = None
    student_labels: list[LessonStudentLabelDTO] = Field(default_factory=list)
    id: int
    course_id: int
    teacher_user_id: int
    title: str
    topic: str | None = None
    description: str | None = None
    scheduled_at: datetime
    duration_minutes: int = 55
    status: LessonStatus = Field(default=LessonStatus.SCHEDULED, validation_alias=AliasChoices("effective_status", "status"))
    call_url_override: str | None = None
    effective_call_url: str | None = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False
    deleted_at: datetime | None = None
    has_lecture: bool = False
    has_homework: bool = False
    regular_series_id: UUID | None = None
    regular_original_at: datetime | None = None
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
    expected_updated_at: AwareDatetime | None = None
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


# Regular scheduling is deliberately separate from the single-lesson POST.
from typing import Literal, Self
from uuid import UUID
from pydantic import model_validator


class RegularLessonSpecDTO(CreateLessonRequestDTO):
    student_user_id: int = Field(gt=0)
    status: Literal[LessonStatus.SCHEDULED] = LessonStatus.SCHEDULED


class PreviewRegularLessonsRequestDTO(BaseModel):
    operation_id: UUID
    action: Literal["create", "extend", "stop", "cancel_future"]
    series_id: UUID | None = None
    lesson: RegularLessonSpecDTO | None = None
    weeks: Annotated[int, Field(strict=True, ge=1, le=12)] = 4
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def valid_action(self) -> Self:
        if self.action == "create":
            if self.lesson is None or self.series_id is not None:
                raise ValueError("Create requires lesson and no series_id")
        elif self.series_id is None or self.lesson is not None:
            raise ValueError("This action requires series_id and no lesson")
        if self.action in ("stop", "cancel_future") and "weeks" in self.model_fields_set:
            raise ValueError("weeks is only used for create/extend")
        return self


class ConfirmRegularLessonsRequestDTO(BaseModel):
    preview_revision: int = Field(strict=True, gt=0)
    acknowledge_conflicts: bool = Field(default=False, strict=True)
    model_config = ConfigDict(extra="forbid")


class RegularOccurrencePreviewDTO(BaseModel):
    scheduled_at: AwareDatetime
    duration_minutes: int
    lesson_id: int | None = None
    conflict_lesson_ids: list[int] = Field(default_factory=list)
    conflict_occurrence_dates: list[AwareDatetime] = Field(default_factory=list)


class RegularPreviewDTO(BaseModel):
    course_id: int
    student_user_id: int
    title: str
    timezone: Literal["Europe/Moscow"] = "Europe/Moscow"
    occurrences: list[RegularOccurrencePreviewDTO]
    count: int
    last_date: AwareDatetime | None
    series_revision: int | None = None


class RegularOperationResultDTO(BaseModel):
    series_id: UUID
    lesson_ids: list[int]
    series_revision: int
    stopped: bool


class RegularOperationResponseDTO(BaseModel):
    operation_id: UUID
    action: Literal["create", "extend", "stop", "cancel_future"]
    state: Literal["preview", "committed"]
    preview_revision: int
    preview: RegularPreviewDTO
    result: RegularOperationResultDTO | None = None


class RegularSeriesResponseDTO(ORMDTO):
    id: UUID
    course_id: int
    student_user_id: int
    spec: RegularLessonSpecDTO
    anchor_at: datetime
    through_at: datetime
    revision: int
    stopped: bool
