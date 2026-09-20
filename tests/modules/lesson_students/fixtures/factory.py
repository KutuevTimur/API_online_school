from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.lesson_students.models import LessonStudent
from src.modules.lesson_students.models_dto import LessonStudentResponseDTO
from tests.modules.lesson_students.fixtures.models_dto import CreateLessonStudentFixtureDTO

from tests.modules.users.fixtures.factory import create_user_factory
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from src.modules.users.models import UserRole
from src.modules.students.models import Student

from tests.modules.lessons.fixtures.factory import create_lesson_factory
from tests.modules.lessons.fixtures.models_dto import CreateLessonFixtureDTO


async def create_lesson_student_factory(
    session_db: AsyncSession,
    crypto_context: CryptContext,
    new_lesson_student: CreateLessonStudentFixtureDTO,
) -> LessonStudentResponseDTO:
    if new_lesson_student.student_id is None:
        user = await create_user_factory(session_db, crypto_context, CreateUserFixtureDTO(role=UserRole.STUDENT))
        result = await session_db.execute(select(Student).where(Student.user_id == user.id))
        student = result.scalar_one()
        new_lesson_student.student_id = student.id

    if new_lesson_student.lesson_id is None:
        lesson = await create_lesson_factory(session_db, crypto_context, CreateLessonFixtureDTO())
        new_lesson_student.lesson_id = lesson.id

    lesson_student_db = LessonStudent(**new_lesson_student.model_dump())
    session_db.add(lesson_student_db)
    await session_db.commit()
    await session_db.refresh(lesson_student_db)

    return LessonStudentResponseDTO.model_validate(lesson_student_db)
