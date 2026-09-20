import pytest_asyncio

from src.modules.student_courses.models_dto import StudentCourseResponseDTO
from tests.helpers import test_crypto_context
from tests.modules.student_courses.fixtures.factory import create_student_course_factory
from tests.modules.student_courses.fixtures.models_dto import CreateStudentCourseFixtureDTO


@pytest_asyncio.fixture(scope="function")
async def create_student_course_fixture(not_open_session_db):
    async def _factory(
        new_student_course: CreateStudentCourseFixtureDTO = CreateStudentCourseFixtureDTO(),
    ) -> StudentCourseResponseDTO:
        async with not_open_session_db() as session:
            student_course = await create_student_course_factory(
                session_db=session,
                crypto_context=test_crypto_context,
                new_student_course=new_student_course,
            )
            return student_course

    return _factory
