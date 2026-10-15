from src.modules.files.models_dto import StorageQuotaResponse
from functools import wraps
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.exception import NotFoundData
from src.modules.files.models import FileAsset
from src.modules.files.repository import FileAssetsRepository, StorageQuotaRepository
from src.modules.handlers_files.handler_documents import HandlerDocuments
from src.modules.storage.download import safe_display_name
from src.modules.storage.service import LegacyStorage, LocalStorage


class FileAssetsService:
    def __init__(self, session: AsyncSession, handler: HandlerDocuments) -> None:
        self.repo = FileAssetsRepository(session)
        self.session = session
        self.handler = handler

    async def register(self, original: Path, download: Path, display_name: str,
                       uploader_user_id: int, recipient_user_id: int | None = None) -> tuple[int, int]:
        quota = StorageQuotaRepository(self.session)
        owner = recipient_user_id or uploader_user_id
        limit = await quota.lock_limit(owner)
        ids = {}
        for path in dict.fromkeys([original, download]):
            info, mime = self.handler.saved_objects[path]
            asset = FileAsset(backend='local', key=LegacyStorage(self.handler.config.paths).key(path),
                              size=info.size, sha256=info.sha256, mime=mime,
                              display_name=safe_display_name(display_name if path == original else Path(display_name).stem + download.suffix),
                              state='ready', uploader_user_id=uploader_user_id)
            self.session.add(asset)
            await self.session.flush()
            ids[path] = asset.id
        if (original != download and self.handler.config.photo_originals_approved
                and self.handler.saved_objects[original][1].startswith('image/')):
            from src.modules.course_lifecycle.models import FileDeletion
            self.session.add(FileDeletion(path=str(original)))
            await self.repo.prune({ids[original]})
            ids[original] = ids[download]
        pending = self.handler.quota_pending.setdefault(owner,set())
        pending.update(ids.values())
        if await quota.usage(owner,pending) > limit:
            from src.modules.handlers_files.exception import FileTooLarge
            raise FileTooLarge("Student storage quota exceeded; ask an administrator to increase it")
        return ids[original], ids[download]

    async def download(self, asset_id: int | None, legacy_path: str | None,
                       legacy_name: str | None) -> tuple[str | None, str | None, str]:
        if asset_id is None:
            if not self.handler.config.legacy_file_reads:
                raise NotFoundData()
            return legacy_path, legacy_name, 'application/pdf'
        asset = await self.repo.ready(asset_id)
        if asset is None or asset.backend != 'local':
            raise NotFoundData()
        LocalStorage.parts(asset.key)
        return str(self.handler.config.paths.media / asset.key), asset.display_name, asset.mime


async def discard_uploads(session: AsyncSession, handler: HandlerDocuments, paths: list[Path]) -> None:
    """Compensate only new UUID objects; durable retry if unlink fails."""
    from src.modules.course_lifecycle.models import FileDeletion
    from src.modules.course_lifecycle.repository import LifecycleRepository
    # A connection can lose COMMIT acknowledgement after the DB committed.
    # Confirm absence of durable references before any compensation unlink.
    try:
        repo = LifecycleRepository(session)
        referenced = {Path(p) for p in await repo.referenced_paths()}
        referenced.update(handler.config.paths.media/key for key in await repo.asset_keys())
    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass
        # Unknown DB outcome: retain bytes for the 24h reconciliation pass.
        return
    storage = LocalStorage(handler.config.paths)
    legacy = LegacyStorage(handler.config.paths)
    failed = []
    for path in dict.fromkeys(paths):
        if path in referenced:
            continue
        try:
            await storage.delete(legacy.key(path))
        except (OSError, ValueError):
            failed.append(path)
    if failed:
        session.add_all([FileDeletion(path=str(p)) for p in failed])
        await session.commit()


def atomic_file_upload(method):
    """Teacher upload methods mark the point of successful DB commit explicitly."""
    @wraps(method)
    async def wrapped(self, *args, **kwargs):
        handler = self.handler_documents
        handler.upload_committed = False
        handler.saved_objects.clear()
        handler.quota_pending.clear()
        handler.transient_objects.clear()
        try:
            return await method(self, *args, **kwargs)
        except BaseException:
            if not handler.upload_committed:
                await self.session_db.rollback()
                await discard_uploads(self.session_db, handler, list(handler.saved_objects) + handler.transient_objects)
            raise
    return wrapped


class StorageQuotaService:
    def __init__(self,session: AsyncSession) -> None:
        self.session=session
        self.repo=StorageQuotaRepository(session)

    async def report(self,user_id: int) -> StorageQuotaResponse:
        limit=await self.repo.lock_limit(user_id)
        usage=await self.repo.usage(user_id)
        ratio=usage/limit
        return StorageQuotaResponse.model_validate({'user_id':user_id,'limit_bytes':limit,'used_bytes':usage,
                'warning':'full' if ratio>=1 else 'critical' if ratio>=.85 else 'near_limit' if ratio>=.70 else None,
                'courses':await self.repo.courses(user_id)})

    async def report_for(self,actor_id: int,role,user_id: int) -> StorageQuotaResponse:
        from src.modules.users.models import UserRole
        from src.modules.check_permission.exception import PermissionErrorService
        if actor_id != user_id and role != UserRole.ADMIN:
            raise PermissionErrorService()
        return await self.report(user_id)

    async def change(self,actor_id: int,user_id: int,limit: int) -> StorageQuotaResponse:
        from src.modules.course_lifecycle.models import LifecycleAudit
        from uuid import uuid4
        from src.modules.check_permission.service import ObjectPermissionService
        from src.modules.check_permission.exception import PermissionErrorService
        from src.modules.users.models import UserRole
        if (await ObjectPermissionService(self.session).actor(actor_id)).role != UserRole.ADMIN:
            raise PermissionErrorService()
        try:
            await self.repo.lock_limit(user_id)
            await self.repo.set_limit(user_id,limit)
            self.session.add(LifecycleAudit(actor_user_id=actor_id,object_type='user',object_id=user_id,
                action='file_quota',correlation_id=uuid4().hex))
            result=await self.report(user_id)
            await self.session.commit()
            return result
        except Exception:
            await self.session.rollback()
            raise
