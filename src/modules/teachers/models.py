from datetime import datetime
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import String, func, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from src.core.database.database import Base

if TYPE_CHECKING:
    from src.modules.users.models import User
    from src.modules.courses.models import Course
    from src.modules.lessons.models import Lesson
    from src.modules.homework_submissions.models import HomeworkSubmission


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    avatar_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="teacher")
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="teacher")
    lessons: Mapped[List["Lesson"]] = relationship("Lesson", back_populates="teacher")
    checked_submissions: Mapped[List["HomeworkSubmission"]] = relationship(
        "HomeworkSubmission", 
        back_populates="teacher"
    )
