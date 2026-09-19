from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.courses.repository import CourseRepository
from src.modules.students.repository import StudentRepository
from src.modules.student_courses.repository import StudentCoursesRepository
from src.modules.student_courses.service import StudentCoursesService

def get_student_courses_service(
    session_db: AsyncSession = Depends(get_db),
) -> StudentCoursesService:
    return StudentCoursesService(
        student_courses_repo=StudentCoursesRepository(session=session_db),
        course_repo=CourseRepository(session=session_db),
        student_repo=StudentRepository(session=session_db),
        session_db=session_db,
    )
