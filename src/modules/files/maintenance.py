"""Local maintenance: exact legacy copying and conservative orphan recovery.

No normalization or deletion of retained legacy source paths occurs here.
Manifests live in private media and must be included in backups.
"""
from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.check_permission.service import ObjectPermissionService
from src.modules.course_lifecycle.models import FileDeletion
from src.modules.course_lifecycle.repository import LifecycleRepository
from src.modules.files.models import FileAsset
from src.modules.files.repository import FileAssetsRepository
from src.modules.handlers_files.handler_documents import HandlerDocuments
from src.modules.handlers_files.exception import InvalidDocumentFormat
from src.modules.homework_submissions.models import HomeworkSubmissionFile
from src.modules.storage.download import safe_display_name
from src.modules.storage.service import LegacyStorage, LocalStorage, file_io
from src.modules.users.models import UserRole



def require_local_maintenance(config: Config) -> None:
    if config.env.mode == 'TEST':
        from src.core.config.test_guard import require_test_config
        require_test_config(config)
        return
    target = (config.env.db_host, config.env.db_port, config.env.db_name, config.env.db_user)
    if config.env.mode != 'DEV' or target not in (
        ('127.0.0.1', '55431', 'lgg_dev', 'lgg_dev_app'),
        ('postgres', '5432', 'lgg_dev', 'lgg_dev_app'),
    ):
        raise RuntimeError('Maintenance is restricted to isolated local dev/test')
    connection = config.db_connection
    url = connection.engine.url
    actual = (url.host,str(url.port),url.database,url.username)
    if actual != target or connection.session_local.kw.get('bind') is not connection.engine:
        raise RuntimeError('Maintenance target/engine/session mismatch')


def write_manifest(storage: LocalStorage, key: str, value: dict) -> None:
    parent,name = storage._parent(key,create=True)
    temporary = name+'.'+uuid4().hex+'.pending'
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600,dir_fd=parent)
        with os.fdopen(fd,'w') as stream:
            json.dump(value,stream,ensure_ascii=False,indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary,name,src_dir_fd=parent,dst_dir_fd=parent)
        os.fsync(parent)
    finally:
        try:
            os.unlink(temporary,dir_fd=parent)
        except FileNotFoundError:
            pass
        os.close(parent)


class LegacyFileMigration:
    def __init__(self, session: AsyncSession, config: Config) -> None:
        require_local_maintenance(config)
        self.session = session
        self.config = config
        self.storage = LocalStorage(config.paths)
        self.legacy = LegacyStorage(config.paths)
        self.handler = HandlerDocuments(config)
        self.repo = FileAssetsRepository(session)

    async def _copy(self, raw: str, name: str, actor_id: int, new_keys: list[str], allow_opaque: bool = False) -> FileAsset:
        source_key = self.legacy.key(raw)
        extension = Path(name or raw).suffix.lstrip('.').lower()
        supported = extension in {'pdf','jpg','jpeg','png','webp','heic','heif'}
        if not supported and not allow_opaque:
            raise ValueError('Legacy format needs explicit review')
        if not supported:
            extension = 'bin'
        key = self.legacy.key(self.config.paths.objects / (uuid4().hex+'.'+extension))
        async with self.storage.open(source_key) as stream:
            class Source:
                async def read(self, size: int = -1) -> bytes:
                    return await file_io(stream.read, size)
            info = await self.storage.put(Source(), key, max_bytes=100*1024*1024)
        new_keys.append(key)
        try:
            if not supported:
                raise InvalidDocumentFormat('Opaque legacy format')
            mime = await self.handler.inspect_document(self.config.paths.media/key, extension)
        except InvalidDocumentFormat:
            if not allow_opaque:
                raise
            # Explicit local synthetic import only: preserve old bytes as an
            # attachment, never claim they are a valid PDF/image or normalize them.
            mime = 'application/octet-stream'
        async with self.storage.open(key) as stream:
            def checksum() -> str:
                digest = hashlib.sha256()
                while chunk := stream.read(65536):
                    digest.update(chunk)
                return digest.hexdigest()
            if await file_io(checksum) != info.sha256:
                raise ValueError('Copied checksum mismatch')
        asset = FileAsset(backend='local', key=key, size=info.size, sha256=info.sha256,
                          mime=mime, display_name=safe_display_name(name), state='ready',
                          uploader_user_id=actor_id)  # Actor imports the object; no guessed historical uploader.
        self.session.add(asset)
        await self.session.flush()
        return asset

    async def run(self, actor_id: int, *, apply: bool = False, limit: int = 100,
                  allow_opaque: bool = False) -> dict[str, int]:
        actor = await ObjectPermissionService(self.session).actor(actor_id)
        if actor.role != UserRole.ADMIN:
            raise PermissionErrorService()
        candidates = await self.repo.legacy_candidates(limit)
        await self.session.rollback()
        result = {'candidates':len(candidates), 'migrated':0, 'failed':0}
        if not apply:
            return result
        for model, object_id in candidates:
            keys = []
            try:
                row = await self.repo.lock_legacy(model,object_id)
                if row is None:
                    continue
                old_paths = sorted({row.original_file_path, row.pdf_file_path} - {None, ''})
                copied = {}
                values = {}
                for path_attr, asset_attr, name_attr in (
                    ('original_file_path','original_asset_id','original_file_name'),
                    ('pdf_file_path','download_asset_id','pdf_file_name'),
                ):
                    raw = getattr(row,path_attr)
                    if not raw or getattr(row,asset_attr) is not None:
                        continue
                    if raw not in copied:
                        asset = await self._copy(raw,getattr(row,name_attr),actor_id,keys,allow_opaque)
                        equal = next((a for a in copied.values() if a.sha256 == asset.sha256 and a.mime == asset.mime),None)
                        if equal:
                            await self.session.delete(asset)
                            await self.storage.delete(asset.key)
                            keys.remove(asset.key)
                            asset = equal
                        copied[raw] = asset
                    asset = copied[raw]
                    values[asset_attr] = asset.id
                    values[path_attr] = str(self.config.paths.media/asset.key)
                    if model is HomeworkSubmissionFile and asset_attr == 'original_asset_id':
                        values['source_size'] = asset.size
                if not values:
                    await self.session.rollback()
                    continue
                if hasattr(row, 'updated_at'):
                    values['updated_at'] = row.updated_at
                manifest = {'state':'prepared','model':model.__tablename__,'id':object_id,
                            'course_id':await self.repo.owner_course(model,object_id),
                            'retained_until':(datetime.now(UTC)+timedelta(days=7)).isoformat(),
                            'legacy_fields':{name:getattr(row,name) for name in (
                                'original_file_path','pdf_file_path','original_asset_id','download_asset_id')},
                            'new_fields':{k:v for k,v in values.items() if k != 'updated_at'},
                            'retained_paths':old_paths,
                            'objects':[{'key':a.key,'sha256':a.sha256,'size':a.size,'mime':a.mime} for a in {a.id:a for a in copied.values()}.values()]}
                path = self.config.paths.temp/'migration-manifests'/(uuid4().hex+'.json')
                await file_io(write_manifest,self.storage,self.legacy.key(path),manifest)
                await self.repo.bind_legacy(model,object_id,values)
                await self.session.commit()
                result['migrated'] += 1
                # The prepared manifest is sufficient protection after a crash.
                manifest['state'] = 'committed'
                try:
                    await file_io(write_manifest,self.storage,self.legacy.key(path),manifest)
                except OSError:
                    pass
            except Exception:
                await self.session.rollback()
                from src.modules.files.service import discard_uploads
                await discard_uploads(self.session,self.handler,[self.config.paths.media/key for key in keys])
                result['failed'] += 1
        return result


async def manifest_paths(config: Config, session: AsyncSession) -> tuple[set[Path], set[Path]]:
    root = config.paths.temp/'migration-manifests'
    retained, purged = set(), set()
    purged_courses = await FileAssetsRepository(session).purged_courses()
    if root.exists():
        storage = LocalStorage(config.paths)
        for manifest in root.glob('*.json'):
            async with storage.open(LegacyStorage(config.paths).key(manifest)) as stream:
                data = await file_io(stream.read,1024*1024)
            manifest_data = json.loads(data)
            expires = manifest_data.get('retained_until')
            expired = bool(expires and datetime.fromisoformat(expires) <= datetime.now(UTC))
            course_purged = manifest_data.get('course_id') in purged_courses
            if expired and not course_purged and any(Path(p).exists() for p in manifest_data['retained_paths']):
                # Never discard the last correct copy after damage/loss of the new object.
                for obj in manifest_data['objects']:
                    async with storage.open(obj['key']) as stream:
                        def checksum() -> str:
                            digest = hashlib.sha256()
                            while chunk := stream.read(65536):
                                digest.update(chunk)
                            return digest.hexdigest()
                        if await file_io(checksum) != obj['sha256']:
                            raise ValueError('Migration checksum changed; retaining legacy backups')
            target = purged if course_purged or expired else retained
            target.update(Path(p) for p in manifest_data['retained_paths'])
    return retained, purged-retained


async def retained_paths(config: Config, session: AsyncSession) -> set[Path]:
    return (await manifest_paths(config,session))[0]


async def queue_purged_backups(config: Config, session: AsyncSession) -> None:
    _, purged = await manifest_paths(config,session)
    pending = await LifecycleRepository(session).pending_paths()
    # Completed jobs are harmlessly replayable after restart; missing bytes unlink idempotently.
    candidates = [p for p in purged if str(p) not in pending and p.exists()]
    session.add_all([FileDeletion(path=str(p)) for p in candidates])
    await session.commit()


class OrphanReconciliation:
    """Only recognizable owned UUID objects, after a 24h crash-recovery grace."""
    def __init__(self, session: AsyncSession, config: Config) -> None:
        require_local_maintenance(config)
        self.session, self.config = session, config

    async def run(self, *, apply: bool = False, now: datetime | None = None) -> dict[str, int]:
        repo = LifecycleRepository(self.session)
        referenced = {Path(p) for p in await repo.referenced_paths()}
        referenced.update(self.config.paths.media/k for k in await repo.asset_keys())
        referenced.update(await retained_paths(self.config,self.session))
        referenced.update(Path(p) for p in await repo.pending_paths())
        cutoff = (now or datetime.now(UTC))-timedelta(hours=24)
        def scan() -> list[Path]:
            found = []
            roots = [self.config.paths.objects,self.config.paths.lectures,self.config.paths.homework,
                     self.config.paths.homework_submissions,self.config.paths.temp]
            pattern = re.compile(r'(?:[0-9a-f]{32}(?:\.[a-z0-9]+)?|\.upload-[0-9a-f]{32})\Z')
            for directory in roots:
                if directory.is_symlink():
                    raise ValueError('Unsafe reconciliation root')
                for parent, dirs, files in os.walk(directory, followlinks=False):
                    dirs[:] = [d for d in dirs if not (Path(parent)/d).is_symlink() and d != 'migration-manifests']
                    for name in files:
                        path = Path(parent)/name
                        if pattern.fullmatch(name) and path not in referenced and not path.is_symlink():
                            if path.stat().st_mtime < cutoff.timestamp():
                                found.append(path)
            return found
        found = await file_io(scan)
        if apply:
            self.session.add_all([FileDeletion(path=str(p)) for p in found])
            await self.session.commit()
        return {'orphan_candidates':len(found), 'queued':len(found) if apply else 0}
