from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database.database import get_db
from src.modules.notifications.service import NotificationsService


def get_notifications_service(session: AsyncSession = Depends(get_db)) -> NotificationsService:
    return NotificationsService(session)
