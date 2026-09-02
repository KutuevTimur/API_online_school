import pytest_asyncio

from src.core.config import Config
from src.modules.courses.models_dto import CoursesDTO
from tests.helpers import test_crypto_context
from tests.modules.courses.fixtures.factory import create_course_factory
from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO


@pytest_asyncio.fixture(scope="function")
async def create_course_fixture(
    config_fix: Config,
    not_open_session_db,
):
    """
    :return: Возвращает функцию-фабрику -> функция возвращает `CoursesDTO`
    """

    async def _factory(
        new_course: CreateCourseFixtureDTO = CreateCourseFixtureDTO(),
    ) -> CoursesDTO:
        async with not_open_session_db() as session:
            course = await create_course_factory(
                session_db=session,
                crypto_context=test_crypto_context,
                new_course=new_course,
            )
            return course

    return _factory
