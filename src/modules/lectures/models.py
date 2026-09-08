from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from src.core.database.database import Base

if TYPE_CHECKING:
    from src.modules.lesson_students.models import LessonStudent


class Lecture(Base):
    __tablename__ = "lectures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lesson_student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("lesson_students.id"),
        nullable=False,
    )

    original_file_path: Mapped[str] = mapped_column(String, nullable=False)
    original_file_name: Mapped[str] = mapped_column(String, nullable=False)
    original_file_type: Mapped[str] = mapped_column(String, nullable=False)

    pdf_file_path: Mapped[str] = mapped_column(String, nullable=False)
    pdf_file_name: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    lesson_student: Mapped["LessonStudent"] = relationship(
        "LessonStudent",
        back_populates="lecture"
    )
