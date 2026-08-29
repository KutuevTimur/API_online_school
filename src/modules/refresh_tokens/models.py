from datetime import datetime

from sqlalchemy import DateTime, String, Integer, func, ForeignKey, Boolean, text
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.orm.attributes import Mapped

from src.core.database.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    refresh_token_id: Mapped[int] = mapped_column(Integer,autoincrement=True,primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer,ForeignKey("users.id"),nullable=False)
    token: Mapped[str] = mapped_column(String(512),unique=True,nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean,nullable=False,server_default=text("false"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())

    user: Mapped["Users"] = relationship(
        "Users",
        back_populates="refresh_tokens"
    )