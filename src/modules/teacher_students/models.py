from datetime import datetime
from sqlalchemy import ForeignKey, Integer, DateTime, UniqueConstraint, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database.database import Base


class TeacherStudent(Base):
    __tablename__ = "teacher_students"
    __table_args__ = (
        UniqueConstraint("teacher_id", "student_id", name="uq_teacher_students_pair"),
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="ck_teacher_students_dates"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
