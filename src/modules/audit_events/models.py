from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_event_created", "created_at", "id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(32))
    object_type: Mapped[str] = mapped_column(String(32))
    object_id: Mapped[int] = mapped_column(Integer)
    result: Mapped[str] = mapped_column(String(16), default="success")
    correlation_id: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
