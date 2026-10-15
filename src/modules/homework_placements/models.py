from datetime import datetime
from sqlalchemy import Integer, ForeignKey, String, DateTime, UniqueConstraint, CheckConstraint, Index, text, func
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database.database import Base


class HomeworkPlacement(Base):
    __tablename__ = "homework_placements"
    __table_args__ = (
        UniqueConstraint("homework_id", "lesson_student_id", name="uq_homework_placement"),
        CheckConstraint("kind IN ('original', 'debt')", name="ck_placement_kind"),
        Index("uix_homework_original_placement", "homework_id", unique=True,
              postgresql_where=text("kind = 'original'")),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homeworks.id", ondelete="CASCADE"), index=True)
    lesson_student_id: Mapped[int] = mapped_column(ForeignKey("lesson_students.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    due_lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id"), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HomeworkDeadlineEvent(Base):
    __tablename__ = "homework_deadline_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    placement_id: Mapped[int] = mapped_column(ForeignKey("homework_placements.id", ondelete="CASCADE"), index=True)
    lesson_student_id: Mapped[int] = mapped_column(ForeignKey("lesson_students.id"))
    due_lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id"), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
