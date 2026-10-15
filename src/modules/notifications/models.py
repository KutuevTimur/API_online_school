from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, func, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database.database import Base


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("recipient_user_id", "dedupe_key", name="uq_notification_recipient_event"),
        Index("ix_notification_recipient_created", "recipient_user_id", "created_at", "id"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipient_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    event_type: Mapped[str] = mapped_column(String(32))
    object_type: Mapped[str] = mapped_column(String(32))
    object_id: Mapped[int] = mapped_column(Integer)  # retained when target is purged
    dedupe_key: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
