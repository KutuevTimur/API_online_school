from datetime import date
from sqlalchemy import ForeignKey, Integer, Date, Boolean, String, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database.database import Base


class WeeklyLessonNorm(Base):
    __tablename__ = 'weekly_lesson_norms'
    __table_args__ = (
        UniqueConstraint('teacher_id', 'student_id', 'week', 'kind', name='uq_weekly_norm'),
        CheckConstraint("kind IN ('regular', 'exception')", name='ck_weekly_norm_kind'),
        CheckConstraint('target IS NULL OR target > 0', name='ck_weekly_norm_positive'),
        CheckConstraint('EXTRACT(ISODOW FROM week) = 1', name='ck_weekly_norm_monday'),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey('teachers.id'))
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'))
    week: Mapped[date] = mapped_column(Date)
    kind: Mapped[str] = mapped_column(String(12))
    target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    paused: Mapped[bool] = mapped_column(Boolean, default=False, server_default='false')
