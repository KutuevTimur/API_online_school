from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.modules.student_courses.models import StudentCourse
from src.modules.student_courses.models_dto import StudentCourseResponseDTO
from tests.modules.student_courses.fixtures.models_dto import CreateStudentCourseFixtureDTO

from tests.modules.users.fixtures.factory import create_user_factory
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from src.modules.users.models import UserRole
from src.modules.students.models import Student

from tests.modules.courses.fixtures.factory import create_course_factory
from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO


async def create_student_course_factory(
    session_db: AsyncSession,
    crypto_context: CryptContext,
    new_student_course: CreateStudentCourseFixtureDTO,
) -> StudentCourseResponseDTO:
    if new_student_course.student_id is None:
        user = await create_user_factory(session_db, crypto_context, CreateUserFixtureDTO(role=UserRole.STUDENT))
        result = await session_db.execute(select(Student).where(Student.user_id == user.id))
        student = result.scalar_one()
        new_student_course.student_id = student.id

    if new_student_course.course_id is None:
        course = await create_course_factory(session_db, crypto_context, CreateCourseFixtureDTO())
        new_student_course.course_id = course.id

    student_course_db = StudentCourse(**new_student_course.model_dump())
    session_db.add(student_course_db)
    await session_db.commit()
    stmt = select(StudentCourse).options(joinedload(StudentCourse.student)).where(StudentCourse.id == student_course_db.id)
    res = await session_db.execute(stmt)
    student_course_db = res.scalar_one()

    return StudentCourseResponseDTO.model_validate(student_course_db)
