import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.config import Config


@pytest_asyncio.fixture(scope="function")
async def session_db(config_fix: Config):
    engine = create_async_engine(config_fix.db_connection.sql_db_url)

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def not_open_session_db(config_fix: Config) -> sessionmaker:
    engine = create_async_engine(config_fix.db_connection.sql_db_url)

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )

    return async_session