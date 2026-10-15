from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database.database import get_db
from src.modules.files.service import StorageQuotaService


def get_storage_quota_service(session: AsyncSession=Depends(get_db)) -> StorageQuotaService:
    return StorageQuotaService(session)
