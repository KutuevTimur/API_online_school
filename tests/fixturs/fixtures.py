import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from helpers import test_crypto_context
from src.core.config import create_config, Config
from src.core.database.database import get_db
from src.modules.api.app import init_fastapi_app
from src.modules.depends import get_config


@pytest_asyncio.fixture(scope="session", autouse=True)
async def lifespan_for_tests(app_fastapi: FastAPI):
    async with app_fastapi.router.lifespan_context(app_fastapi):
        app_fastapi.state.cr_context = test_crypto_context
        yield


@pytest_asyncio.fixture(scope="session")
async def app_fastapi(config_fix: Config):
    app = init_fastapi_app(config=config_fix)
    app.dependency_overrides[get_config] = lambda: config_fix
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="session")
async def config_fix(tmp_path_factory):
    conf = create_config(test=True, media_root=tmp_path_factory.mktemp("lgg-test-media"))
    try:
        yield conf
    finally:
        await conf.db_connection.engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleaning_paths_fix():
    # pytest owns and retires tmp_path_factory directories; never rmtree media roots.
    yield


@pytest_asyncio.fixture
async def client_for_tests(not_open_session_db, app_fastapi: FastAPI, config_fix: Config):
    async with not_open_session_db() as session_db:
        app_fastapi.dependency_overrides[get_db] = lambda: session_db
        try:
            async with AsyncClient(transport=ASGITransport(app_fastapi), base_url="http://test") as ac:
                yield ac
        finally:
            app_fastapi.dependency_overrides.pop(get_db, None)
