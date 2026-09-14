from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from src.core.database.database import Base

if TYPE_CHECKING:
    from src.modules.lesson_students.models import LessonStudent


class Homework(Base):
    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lesson_student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("lesson_students.id"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    original_file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    original_file_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    original_file_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    pdf_file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    pdf_file_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    lesson_student: Mapped["LessonStudent"] = relationship(
        "LessonStudent",
        back_populates="homeworks"
    )
