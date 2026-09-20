import pytest_asyncio

from src.modules.lesson_students.models_dto import LessonStudentResponseDTO
from tests.helpers import test_crypto_context
from tests.modules.lesson_students.fixtures.factory import create_lesson_student_factory
from tests.modules.lesson_students.fixtures.models_dto import CreateLessonStudentFixtureDTO


@pytest_asyncio.fixture(scope="function")
async def create_lesson_student_fixture(not_open_session_db):
    async def _factory(
        new_lesson_student: CreateLessonStudentFixtureDTO = CreateLessonStudentFixtureDTO(),
    ) -> LessonStudentResponseDTO:
        async with not_open_session_db() as session:
            lesson_student = await create_lesson_student_factory(
                session_db=session,
                crypto_context=test_crypto_context,
                new_lesson_student=new_lesson_student,
            )
            return lesson_student

    return _factory
