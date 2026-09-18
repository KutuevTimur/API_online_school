import enum
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import String, func, Enum, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from src.core.database.database import Base


if TYPE_CHECKING:
    from src.modules.refresh_tokens.models import RefreshToken
    from src.modules.students.models import Student
    from src.modules.teachers.models import Teacher


class UserRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            values_callable=lambda x: [e.value for e in x],
            name="role"
        ),
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="user")
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="user")
    student: Mapped["Student"] = relationship("Student", back_populates="user")