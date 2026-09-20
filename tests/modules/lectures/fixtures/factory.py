from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.lectures.models import Lecture
from src.modules.lectures.models_dto import LectureResponseDTO
from tests.modules.lectures.fixtures.models_dto import CreateLectureFixtureDTO

from tests.modules.lesson_students.fixtures.factory import create_lesson_student_factory
from tests.modules.lesson_students.fixtures.models_dto import CreateLessonStudentFixtureDTO


async def create_lecture_factory(
    session_db: AsyncSession,
    crypto_context: CryptContext,
    new_lecture: CreateLectureFixtureDTO,
) -> LectureResponseDTO:
    if new_lecture.lesson_student_id is None:
        lesson_student = await create_lesson_student_factory(session_db, crypto_context, CreateLessonStudentFixtureDTO())
        new_lecture.lesson_student_id = lesson_student.id

    lecture_db = Lecture(**new_lecture.model_dump())
    session_db.add(lecture_db)
    await session_db.commit()
    await session_db.refresh(lecture_db)

    return LectureResponseDTO.model_validate(lecture_db)
