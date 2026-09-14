from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.lessons.repository import LessonsRepository
from src.modules.lessons.service import LessonsService
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository
from src.modules.courses.repository import CourseRepository


def get_lessons_service(
    session: AsyncSession = Depends(get_db),
) -> LessonsService:
    return LessonsService(
        lessons_repo=LessonsRepository(session=session),
        course_repo=CourseRepository(session=session),
        student_repo=StudentRepository(session=session),
        teacher_repo=TeacherRepository(session=session),
        session_db=session,
    )
