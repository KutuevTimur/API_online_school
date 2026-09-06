from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.core.database.database import get_db
from src.modules.courses.repository import CourseRepository
from src.modules.courses.service import CoursesService
from src.modules.depends import get_config
from src.modules.handlers_files.compression_images import CompressionImages
from src.modules.handlers_files.converter_images import HandlerImages
from src.modules.path_builder import PathBuilder
from src.modules.student_courses.repository import StudentCoursesRepository
from src.modules.students.repository import StudentRepository
from src.modules.students.service import StudentService
from src.modules.teachers.repository import TeacherRepository
from src.modules.teachers.service import TeacherService


def get_courses_service(
    session: AsyncSession = Depends(get_db),
    config: Config = Depends(get_config),
) -> CoursesService:
    teacher_repo = TeacherRepository(session=session)
    student_repo = StudentRepository(session=session)
    student_courses_repo = StudentCoursesRepository(session=session)
    return CoursesService(
        course_repo=CourseRepository(session=session),
        teacher_repo=teacher_repo,
        teacher_service=TeacherService(teacher_repo=teacher_repo, session_db=session),
        student_repo=student_repo,
        student_service=StudentService(student_repo=student_repo, session_db=session),
        student_courses_repo=student_courses_repo,
        path_builder=PathBuilder(config=config),
        handler_images=HandlerImages(config=config),
        compression_images=CompressionImages(config=config),
        session_db=session,
    )
