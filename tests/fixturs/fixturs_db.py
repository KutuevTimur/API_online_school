import pytest_asyncio
from src.core.config import Config
from src.core.config.test_guard import require_test_config


@pytest_asyncio.fixture(scope="function")
async def session_db(config_fix: Config):
    require_test_config(config_fix)
    async with config_fix.db_connection.session_local() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def not_open_session_db(config_fix: Config):
    require_test_config(config_fix)
    return config_fix.db_connection.session_local
