"""Durable access gaps, admin audit and file deletion outbox."""
from datetime import datetime
from sqlalchemy import Integer, String, Text, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database.database import Base


class EnrollmentGap(Base):
    __tablename__ = "enrollment_gaps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("student_courses.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LifecycleAudit(Base):
    __tablename__ = "lifecycle_audit"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    object_type: Mapped[str] = mapped_column(String(32))
    object_id: Mapped[int] = mapped_column(Integer)  # survives target purge
    action: Mapped[str] = mapped_column(String(32))
    result: Mapped[str] = mapped_column(String(16), default="success")
    correlation_id: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FileDeletion(Base):
    __tablename__ = "file_deletions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    path: Mapped[str] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    last_error: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
