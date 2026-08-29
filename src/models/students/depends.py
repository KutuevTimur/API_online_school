from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.models.students.repository import StudentRepository
from src.models.students.service import StudentService


def get_student_service(
    session: AsyncSession = Depends(get_db),
) -> StudentService:
    return StudentService(
        student_repo=StudentRepository(session=session),
        session_db=session,
    )
