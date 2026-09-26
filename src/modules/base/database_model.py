from datetime import datetime, UTC
from typing import TypeVar
from pydantic import BaseModel

from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.database import Base

# Объявляем generic тип, ограниченный классом Base
ModelType = TypeVar("ModelType", bound=Base)
DTOType = TypeVar("DTOType", bound="BaseModel")


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None