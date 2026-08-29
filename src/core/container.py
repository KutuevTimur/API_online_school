from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import create_config

# Не удалять. Используется для подгрузки всех моделей БД
from src.modules.db_models import *


class Container:

    def __init__(self) -> None:
        self.config = create_config()
        self.async_session_factory = self.config.db_connection.session_local

    async def get_db(
        self,
    ) -> AsyncIterator[AsyncSession]:
        async with self.async_session_factory() as session:
            yield session


def create_container() -> Container:
    return Container()
