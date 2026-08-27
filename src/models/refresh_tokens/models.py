from sqlalchemy import Column, DateTime, String, Integer, func, ForeignKey, Boolean, text
from sqlalchemy.orm import relationship

from src.core.database.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    refresh_token_id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(512), unique=True, nullable=False)
    is_revoked = Column(Boolean, nullable=False, server_default=text("false"))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("Users", back_populates="refresh_tokens")