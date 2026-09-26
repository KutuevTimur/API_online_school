from typing import Type, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import ModelType, DTOType


class BaseRepository:

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    def add(self, data: Union[DTOType, dict]) -> ModelType:
        if isinstance(data, dict):
            instance = self.model(**data)
        elif hasattr(data, "model_dump"):
            instance = self.model(**data.model_dump())
        else:
            instance = self.model(**dict(data))
        self.session.add(instance)
        return instance

    async def get_by_id(self, model: ModelType, obj_id: int) -> ModelType | None:
        stmt = select(model).where(model.id == obj_id)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()