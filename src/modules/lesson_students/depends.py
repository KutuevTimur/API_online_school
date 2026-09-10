from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.lesson_students.repository import LessonStudentsRepository
from src.modules.lesson_students.service import LessonStudentsService
from src.modules.lessons.repository import LessonsRepository
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository


def get_lesson_students_service(
    session: AsyncSession = Depends(get_db),
) -> LessonStudentsService:
    return LessonStudentsService(
        lesson_students_repo=LessonStudentsRepository(session=session),
        lessons_repo=LessonsRepository(session=session),
        student_repo=StudentRepository(session=session),
        teacher_repo=TeacherRepository(session=session),
        session_db=session,
    )
