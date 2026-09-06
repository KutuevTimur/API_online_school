from datetime import datetime

from sqlalchemy import func, Boolean, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from src.core.database.database import Base


class TeacherCourse(Base):
    __tablename__ = "teacher_courses"

    __table_args__ = (
        UniqueConstraint("teacher_id", "course_id", name="uq_teacher_courses_teacher_id_course_id"),
        Index("ix_teacher_courses_teacher_id_course_id", "teacher_id", "course_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("teachers.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="teacher_courses")
    course: Mapped["Course"] = relationship("Course", back_populates="teacher_courses")
