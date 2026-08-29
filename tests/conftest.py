import pytest_asyncio

from fixturs import *
from src.modules.db_models import *
from src.tools.creating_db import create_database

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete


@pytest_asyncio.fixture(scope='session', autouse=True)
async def start_test(config_fix, app_fastapi):
    if config_fix.env.mode != "TEST":
        raise RuntimeError("Используется основные .env настройки!")

    await create_database()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clearing_db(session_db: AsyncSession):
    """Очищает базу банных"""
    # удаляем обязательно в таком порядке
    await session_db.execute(delete(RefreshToken))
    await session_db.execute(delete(Teachers))
    await session_db.execute(delete(Students))
    await session_db.execute(delete(Users))
    await session_db.commit()
