from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import Integer, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from src.core.database.database import Base

if TYPE_CHECKING:
    from src.modules.lessons.models import Lesson
    from src.modules.students.models import Student
    from src.modules.lectures.models import Lecture
    from src.modules.homeworks.models import Homework


class LessonStudent(Base):
    __tablename__ = "lesson_students"
    __table_args__ = (
        UniqueConstraint("lesson_id", "student_id", name="uq_lesson_student"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="lesson_students")
    student: Mapped["Student"] = relationship("Student", back_populates="lesson_students", lazy="selectin")

    lectures: Mapped[List["Lecture"]] = relationship("Lecture", back_populates="lesson_student")
    homeworks: Mapped[List["Homework"]] = relationship("Homework", back_populates="lesson_student")

    @property
    def student_user_id(self) -> int | None:
        return self.student.user_id if self.student else None
