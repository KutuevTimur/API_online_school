import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, ForeignKey, String, Text, func, Enum, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from src.core.database.database import Base

if TYPE_CHECKING:
    from src.modules.homeworks.models import Homework
    from src.modules.teachers.models import Teacher


class HomeworkSubmissionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CHECKED = "checked"


class HomeworkSubmission(Base):
    __tablename__ = 'homework_submissions'
    __table_args__ = (
        UniqueConstraint('homework_id', 'attempt_number', name='uix_homework_attempt'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    homework_id: Mapped[int] = mapped_column(Integer, ForeignKey("homeworks.id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)

    original_file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    original_file_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    original_file_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    pdf_file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    pdf_file_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[HomeworkSubmissionStatus] = mapped_column(
        Enum(HomeworkSubmissionStatus, name="homework_submission_status_enum", create_type=False),
        nullable=False,
        default=HomeworkSubmissionStatus.DRAFT
    )

    grade: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    teacher_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("teachers.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    homework: Mapped["Homework"] = relationship("Homework", back_populates="submissions")
    teacher: Mapped[Optional["Teacher"]] = relationship("Teacher", back_populates="checked_submissions")
