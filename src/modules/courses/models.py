import enum
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import String, func, Enum, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from src.core.database.database import Base

if TYPE_CHECKING:
    from src.modules.student_courses.models import StudentCourses


class AvatarCoursesType(str, enum.Enum):
    """
    Если стоит CUSTOM, то необходимо использовать avatar_path. т.к. Пользователь задал кастомную аватарку
    """
    DEFAULT = "default"
    CUSTOM = "custom"
    PYTHON = "python"
    MATHEMATICS = "mathematics"
    RUSSIAN_LANGUAGE = "russian_language"


class Courses(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    avatar_type: Mapped[AvatarCoursesType] = mapped_column(
        Enum(
            AvatarCoursesType,
            values_callable=lambda x: [e.value for e in x],
            name="avatar_type"
        ),
        nullable=False
    )
    avatar_path: Mapped[str] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student_courses: Mapped[List["StudentCourses"]] = relationship("StudentCourses", back_populates="course")
