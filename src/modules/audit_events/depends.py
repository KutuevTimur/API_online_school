from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database.database import get_db
from src.modules.audit_events.service import AuditEventsService


def get_audit_events_service(session: AsyncSession = Depends(get_db)) -> AuditEventsService:
    return AuditEventsService(session)
