from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class NormRequestDTO(BaseModel):
    week: date
    kind: Literal['regular', 'exception'] = 'regular'
    target: int | None = Field(default=None, strict=True, gt=0, le=2147483647)
    paused: bool = Field(default=False, strict=True)
    expected_revision: int = Field(default=0, ge=0, strict=True)
    model_config = ConfigDict(extra='forbid')

    @field_validator('week')
    @classmethod
    def monday(cls, value: date) -> date:
        if value.weekday() != 0:
            raise ValueError('Use Monday of the Moscow week')
        return value


class PlanningStudentDTO(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    username: str
    scheduled_count: int
    target: int | None
    paused: bool
    norm_revision: int
    missing_homework: int
    missing_lecture: int


class RecipientReminderDTO(BaseModel):
    lesson_id: int
    student_user_id: int
    first_name: str
    last_name: str
    course_id: int
    course_name: str
    title: str
    scheduled_at: datetime
    has_homework: bool
    has_lecture: bool
    needs_homework: bool
    needs_lecture: bool
    homework_not_needed: bool
    lecture_not_needed: bool


class ReminderRequestDTO(BaseModel):
    homework_not_needed: bool | None = None
    lecture_not_needed: bool | None = None
    model_config = ConfigDict(extra='forbid')


class LessonPriceDTO(BaseModel):
    lesson_price_kopecks: int | None = Field(ge=0, le=2147483647, strict=True)
    model_config = ConfigDict(extra='forbid')


class UpdateLessonPriceDTO(LessonPriceDTO):
    expected_price_kopecks: int | None = Field(ge=0, le=2147483647, strict=True)


class WeeklyEarningsDTO(BaseModel):
    week: date
    total_kopecks: int
    lesson_count: int
    completed_count: int
    unpriced_count: int
