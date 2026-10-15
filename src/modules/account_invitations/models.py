from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime
from src.core.database.database import Base


class AccountInvitation(Base):
    __tablename__ = "account_invitations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(16))
    digest: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)


class AccountAudit(Base):
    __tablename__ = "account_audit"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(32))
    result: Mapped[str] = mapped_column(String(16), default="success")
    correlation_id: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuthRateLimit(Base):
    __tablename__ = "auth_rate_limits"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    window: Mapped[int] = mapped_column(Integer)
    count: Mapped[int] = mapped_column(Integer)
