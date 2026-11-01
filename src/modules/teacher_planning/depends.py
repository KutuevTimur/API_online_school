from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database.database import get_db
from src.modules.teacher_planning.repository import TeacherPlanningRepository
from src.modules.teacher_planning.service import TeacherPlanningService


def get_teacher_planning_service(session: AsyncSession = Depends(get_db)) -> TeacherPlanningService:
    return TeacherPlanningService(TeacherPlanningRepository(session))
