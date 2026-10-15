from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database.database import get_db
from src.modules.teacher_students.service import TeacherStudentService


def get_teacher_student_service(session: AsyncSession = Depends(get_db)) -> TeacherStudentService:
    return TeacherStudentService(session)
