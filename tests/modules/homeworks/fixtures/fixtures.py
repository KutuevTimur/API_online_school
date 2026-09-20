import pytest_asyncio

from src.modules.homeworks.models_dto import HomeworkResponseDTO
from tests.helpers import test_crypto_context
from tests.modules.homeworks.fixtures.factory import create_homework_factory
from tests.modules.homeworks.fixtures.models_dto import CreateHomeworkFixtureDTO


@pytest_asyncio.fixture(scope="function")
async def create_homework_fixture(not_open_session_db):
    async def _factory(
        new_homework: CreateHomeworkFixtureDTO = CreateHomeworkFixtureDTO(),
    ) -> HomeworkResponseDTO:
        async with not_open_session_db() as session:
            homework = await create_homework_factory(
                session_db=session,
                crypto_context=test_crypto_context,
                new_homework=new_homework,
            )
            return homework

    return _factory
