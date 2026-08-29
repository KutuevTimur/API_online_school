from fastapi import Depends

from src.modules.teachers.repository import TeacherRepository
from src.modules.teachers.service import TeacherService
from src.core.database.database import get_db


def get_teacher_service(
    session = Depends(get_db),
) -> TeacherService:
    return TeacherService(
        teacher_repo=TeacherRepository(session=session),
        session_db=session,
    )