"""Avatar pointer, audit and durable cleanup share the domain transaction."""
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.course_lifecycle.models import FileDeletion


def retire_avatar(session: AsyncSession, path: str | None) -> None:
    if path:
        session.add(FileDeletion(path=path))


def atomic_avatar_upload(method):
    @wraps(method)
    async def wrapped(self, *args, **kwargs):
        handler = self.handler_images
        handler.created_paths.clear()
        handler.upload_committed = False
        try:
            result = await method(self, *args, **kwargs)
        except BaseException:
            if not handler.upload_committed:
                await self.session_db.rollback()
                from src.modules.files.service import discard_uploads
                await discard_uploads(self.session_db, handler, handler.created_paths)
            raise
        # Queue remains durable on unlink/worker failure. Do not turn an already
        # committed update into a client error; the maintenance worker retries it.
        from src.modules.course_lifecycle.repository import LifecycleRepository
        from src.modules.course_lifecycle.service import LifecycleService
        try:
            await LifecycleService(LifecycleRepository(self.session_db), handler.config)._cleanup(100)
        except Exception:
            await self.session_db.rollback()
        return result
    return wrapped
