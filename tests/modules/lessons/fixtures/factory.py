from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.lessons.models import Lesson
from src.modules.lessons.models_dto import LessonDTO
from tests.modules.lessons.fixtures.models_dto import CreateLessonFixtureDTO
from tests.modules.courses.fixtures.factory import create_course_factory
from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO


async def create_lesson_factory(
    session_db: AsyncSession,
    crypto_context: CryptContext,
    new_lesson: CreateLessonFixtureDTO,
) -> LessonDTO:
    if new_lesson.course_id is None:
        dto = CreateCourseFixtureDTO()
        if new_lesson.teacher_id is not None:
            dto.teacher_id = new_lesson.teacher_id
            
        course = await create_course_factory(session_db, crypto_context, dto)
        new_lesson.course_id = course.id
        new_lesson.teacher_id = course.teacher_id

    if new_lesson.teacher_id is None:
        pass

    lesson_db = Lesson(
        course_id=new_lesson.course_id,
        teacher_id=new_lesson.teacher_id,
        title=new_lesson.title,
        topic=new_lesson.topic,
        description=new_lesson.description,
        scheduled_at=new_lesson.scheduled_at,
        duration_minutes=new_lesson.duration_minutes,
    )
    session_db.add(lesson_db)
    await session_db.commit()
    await session_db.refresh(lesson_db)

    return LessonDTO.model_validate(lesson_db)
