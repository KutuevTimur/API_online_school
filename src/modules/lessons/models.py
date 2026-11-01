import enum
from datetime import datetime, timedelta
from uuid import UUID
from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, String, Text, func, DateTime, Enum, CheckConstraint, UniqueConstraint, Boolean, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship, column_property
from sqlalchemy import case, and_, literal, cast
from typing import List

from src.core.database.database import Base


if TYPE_CHECKING:
    from src.modules.courses.models import Course
    from src.modules.teachers.models import Teacher
    from src.modules.lesson_students.models import LessonStudent


from src.modules.base.database_model import SoftDeleteMixin


class LessonStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Lesson(Base, SoftDeleteMixin):
    __tablename__ = "lessons"
    __table_args__ = (
        CheckConstraint("lesson_price_kopecks >= 0", name="ck_lesson_price"),
        CheckConstraint("duration_minutes > 0", name="ck_lesson_duration_positive"),
        UniqueConstraint("regular_series_id", "regular_original_at", name="uq_lesson_regular_occurrence"),
        CheckConstraint("(regular_series_id IS NULL) = (regular_original_at IS NULL)", name="ck_lesson_regular_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("teachers.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    topic: Mapped[str] = mapped_column(String(1000), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="55")
    status: Mapped[LessonStatus] = mapped_column(
        Enum(LessonStatus, values_callable=lambda values: [v.value for v in values], name="lesson_status"),
        nullable=False, server_default="scheduled")
    # Derived at statement time: no scheduler and no hidden writes during GET.
    effective_status: Mapped[str] = column_property(case(
        (and_(status == LessonStatus.SCHEDULED,
              scheduled_at + duration_minutes * literal(timedelta(minutes=1)) <= func.statement_timestamp()),
         literal(LessonStatus.COMPLETED.value)),
        else_=cast(status, String),
    ))
    lesson_price_kopecks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    call_url_override: Mapped[str | None] = mapped_column(Text, nullable=True)

    regular_series_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("regular_lesson_series.id", name="fk_lesson_regular_series"), nullable=True)
    regular_original_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="lessons", lazy="selectin")
    course: Mapped["Course"] = relationship("Course", back_populates="lessons", lazy="selectin")
    
    lesson_students: Mapped[List["LessonStudent"]] = relationship("LessonStudent", back_populates="lesson")

    @property
    def teacher_user_id(self) -> int | None:
        return self.teacher.user_id if self.teacher else None

    @property
    def effective_call_url(self) -> str | None:
        return self.call_url_override or (self.course.call_url if self.course else None)


class RegularLessonSeries(Base):
    __tablename__ = "regular_lesson_series"
    __table_args__ = (
        UniqueConstraint("teacher_id", "course_id", "student_user_id", "anchor_at", name="uq_regular_series_anchor"),
        CheckConstraint("through_at >= anchor_at", name="ck_regular_series_range"),
        CheckConstraint("revision > 0", name="ck_regular_series_revision"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    student_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    spec: Mapped[dict] = mapped_column(JSON, nullable=False)
    anchor_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    through_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    stopped: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RegularLessonOperation(Base):
    """Durable preview, idempotency key and recovery receipt; committed atomically."""
    __tablename__ = "regular_lesson_operations"
    __table_args__ = (CheckConstraint("preview_revision > 0", name="ck_regular_operation_revision"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    series_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("regular_lesson_series.id", ondelete="CASCADE"), nullable=True)
    request: Mapped[dict] = mapped_column(JSON, nullable=False)
    preview: Mapped[dict] = mapped_column(JSON, nullable=False)
    preview_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
