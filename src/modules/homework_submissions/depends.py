from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.core.database.database import get_db
from src.modules.depends import get_config
from src.modules.handlers_files.handler_documents import HandlerDocuments
from src.modules.homework_submissions.repository import HomeworkSubmissionsRepository
from src.modules.homework_submissions.service import HomeworkSubmissionsService
from src.modules.homeworks.repository import HomeworksRepository
from src.modules.path_builder.service import PathBuilder
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository


def get_homework_submissions_service(
    session: AsyncSession = Depends(get_db),
    config: Config = Depends(get_config),
) -> HomeworkSubmissionsService:
    return HomeworkSubmissionsService(
        homework_submissions_repo=HomeworkSubmissionsRepository(session=session),
        homeworks_repo=HomeworksRepository(session=session),
        path_builder=PathBuilder(config=config),
        handler_documents=HandlerDocuments(config=config),
        teacher_repo=TeacherRepository(session=session),
        student_repo=StudentRepository(session=session),
        session_db=session,
    )
