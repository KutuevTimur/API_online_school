from datetime import datetime

from sqlalchemy import func, Boolean, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from src.core.database.database import Base
from src.modules.base.database_model import SoftDeleteMixin


class StudentCourse(Base, SoftDeleteMixin):
    __tablename__ = "student_courses"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    access_ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    history_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student: Mapped["Student"] = relationship("Student", back_populates="student_courses")
    course: Mapped["Course"] = relationship("Course", back_populates="student_courses")

    @property
    def student_user_id(self) -> int | None:
        return self.student.user_id if self.student else None
