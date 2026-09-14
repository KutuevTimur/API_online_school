from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.core.database.database import get_db
from src.modules.depends import get_config
from src.modules.handlers_files.handler_documents import HandlerDocuments
from src.modules.homeworks.repository import HomeworksRepository
from src.modules.homeworks.service import HomeworksService
from src.modules.lesson_students.repository import LessonStudentsRepository
from src.modules.lessons.repository import LessonsRepository
from src.modules.path_builder.service import PathBuilder
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository


def get_homeworks_service(
    session: AsyncSession = Depends(get_db),
    config: Config = Depends(get_config),
) -> HomeworksService:
    return HomeworksService(
        homeworks_repo=HomeworksRepository(session=session),
        lesson_students_repo=LessonStudentsRepository(session=session),
        lessons_repo=LessonsRepository(session=session),
        student_repo=StudentRepository(session=session),
        teacher_repo=TeacherRepository(session=session),
        path_builder=PathBuilder(config=config),
        handler_documents=HandlerDocuments(config=config),
        session_db=session,
    )
