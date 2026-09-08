from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, String, Text, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.database import Base


if TYPE_CHECKING:
    from src.modules.courses.models import Course
    from src.modules.teachers.models import Teacher


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("teachers.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    topic: Mapped[str] = mapped_column(String(1000), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    duration_minutes: Mapped[datetime] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="lessons", lazy="selectin")
    course: Mapped["Course"] = relationship("Course", back_populates="lessons")

    @property
    def teacher_user_id(self) -> int | None:
        return self.teacher.user_id if self.teacher else None
