from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import Config
from src.core.database.database import get_db
from src.modules.depends import get_config
from src.modules.course_lifecycle.repository import LifecycleRepository
from src.modules.course_lifecycle.service import LifecycleService


def get_lifecycle_service(session: AsyncSession = Depends(get_db),
                          config: Config = Depends(get_config)) -> LifecycleService:
    return LifecycleService(LifecycleRepository(session), config)
