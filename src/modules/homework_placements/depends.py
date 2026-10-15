from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database.database import get_db
from src.modules.homework_placements.service import HomeworkPlacementsService


def get_homework_placements_service(session: AsyncSession = Depends(get_db)) -> HomeworkPlacementsService:
    return HomeworkPlacementsService(session)
