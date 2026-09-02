from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from helpers.functions import random_string
from src.modules.courses.models import Courses, AvatarCoursesType
from src.modules.courses.models_dto import CoursesDTO
from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO


async def create_course_factory(
    session_db: AsyncSession,
    crypto_context: CryptContext = None,
    new_course: CreateCourseFixtureDTO = CreateCourseFixtureDTO(),
) -> CoursesDTO:
    course = Courses(
        name=f"Course_{random_string(8)}" if new_course.name is None else new_course.name,
        slug=f"slug-{random_string(8).lower()}" if new_course.slug is None else new_course.slug,
        description=new_course.description if new_course.description is not None else f"Description {random_string(10)}",
        avatar_type=new_course.avatar_type if new_course.avatar_type is not None else AvatarCoursesType.DEFAULT,
        avatar_path=new_course.avatar_path,
        is_active=new_course.is_active if new_course.is_active is not None else True,
    )
    session_db.add(course)
    await session_db.commit()
    await session_db.refresh(course)

    return CoursesDTO.model_validate(course)
