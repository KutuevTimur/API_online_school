import pytest_asyncio

from src.modules.lectures.models_dto import LectureResponseDTO
from tests.helpers import test_crypto_context
from tests.modules.lectures.fixtures.factory import create_lecture_factory
from tests.modules.lectures.fixtures.models_dto import CreateLectureFixtureDTO


@pytest_asyncio.fixture(scope="function")
async def create_lecture_fixture(not_open_session_db):
    async def _factory(
        new_lecture: CreateLectureFixtureDTO = CreateLectureFixtureDTO(),
    ) -> LectureResponseDTO:
        async with not_open_session_db() as session:
            lecture = await create_lecture_factory(
                session_db=session,
                crypto_context=test_crypto_context,
                new_lecture=new_lecture,
            )
            return lecture

    return _factory
