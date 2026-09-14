import pytest_asyncio

from src.modules.lessons.models_dto import LessonDTO
from tests.helpers import test_crypto_context
from tests.modules.lessons.fixtures.factory import create_lesson_factory
from tests.modules.lessons.fixtures.models_dto import CreateLessonFixtureDTO


@pytest_asyncio.fixture(scope="function")
async def create_lesson_fixture(not_open_session_db):
    async def _factory(
        new_lesson: CreateLessonFixtureDTO = CreateLessonFixtureDTO(),
    ) -> LessonDTO:
        async with not_open_session_db() as session:
            lesson = await create_lesson_factory(
                session_db=session,
                crypto_context=test_crypto_context,
                new_lesson=new_lesson,
            )
            return lesson

    return _factory
