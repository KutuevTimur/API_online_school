import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, String, Text, func, DateTime, Enum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
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
    __table_args__ = (CheckConstraint("duration_minutes > 0", name="ck_lesson_duration_positive"),)

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
    call_url_override: Mapped[str | None] = mapped_column(Text, nullable=True)

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
