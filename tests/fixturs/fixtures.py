import shutil
from typing import AsyncGenerator

import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from helpers import test_crypto_context
from src.core.config import create_config, Config
from src.core.config.config import PathsConfig
from src.core.database.database import get_db
from src.modules.api.app import init_fastapi_app
from src.modules.depends import get_config


@pytest_asyncio.fixture(scope="session", autouse=True)
async def lifespan_for_tests(app_fastapi: FastAPI, config_fix: Config,) -> AsyncGenerator[FastAPI, None]:
    app_fastapi.state.config = config_fix
    app_fastapi.state.cr_context = test_crypto_context


@pytest_asyncio.fixture(scope="session")
async def app_fastapi() -> AsyncGenerator[FastAPI, None]:
    yield init_fastapi_app()


@pytest_asyncio.fixture(scope="session")
async def config_fix() -> AsyncGenerator[Config, None]:
    conf =  create_config()
    conf.paths = PathsConfig.build(postscript="_test")
    yield conf


@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleaning_paths_fix(config_fix) -> AsyncGenerator[None, None]:
    yield
    if config_fix.paths.media.exists():
        shutil.rmtree(config_fix.paths.media, ignore_errors=True)


@pytest_asyncio.fixture
async def client_for_tests(
    not_open_session_db,
    app_fastapi: FastAPI,
    config_fix: Config,
):
    async with not_open_session_db() as session_db:
        app_fastapi.dependency_overrides[get_db] = lambda: session_db # переопределяем Depends(get_db)
        app_fastapi.dependency_overrides[get_config] = lambda: config_fix

        async with AsyncClient(transport=ASGITransport(app_fastapi), base_url="http://test") as ac:
            yield ac
