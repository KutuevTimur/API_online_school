from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.homeworks.models import Homework
from src.modules.homeworks.models_dto import HomeworkResponseDTO
from tests.modules.homeworks.fixtures.models_dto import CreateHomeworkFixtureDTO

from tests.modules.lesson_students.fixtures.factory import create_lesson_student_factory
from tests.modules.lesson_students.fixtures.models_dto import CreateLessonStudentFixtureDTO


async def create_homework_factory(
    session_db: AsyncSession,
    crypto_context: CryptContext,
    new_homework: CreateHomeworkFixtureDTO,
) -> HomeworkResponseDTO:
    if new_homework.lesson_student_id is None:
        lesson_student = await create_lesson_student_factory(session_db, crypto_context, CreateLessonStudentFixtureDTO())
        new_homework.lesson_student_id = lesson_student.id

    homework_db = Homework(**new_homework.model_dump())
    session_db.add(homework_db)
    await session_db.commit()
    await session_db.refresh(homework_db)

    return HomeworkResponseDTO.model_validate(homework_db)
