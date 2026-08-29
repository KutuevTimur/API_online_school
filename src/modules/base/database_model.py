from typing import TypeVar, Type
from pydantic import BaseModel

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import Base

# Объявляем generic тип, ограниченный классом Base
ModelType = TypeVar("ModelType", bound=Base)
DTOType = TypeVar("DTOType", bound="BaseModel")


class BaseRepository:

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    def add(self, data: DTOType) -> ModelType:
        instance = self.model(**data.model_dump())
        self.session.add(instance)
        return instance

    async def get_by_id(self, model: ModelType, obj_id: int) -> ModelType | None:
        stmt = select(model).where(model.id == obj_id)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()
