"""Avatar adapter over T12 immutable storage and bounded image decoder."""
import errno
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from uuid import uuid4

from fastapi import UploadFile

from src.core.config import Config
from src.modules.handlers_files.exception import InvalidImageFormat, InvalidDocumentFormat, FileTooLarge, ImageConversionError
from src.modules.handlers_files.handler_documents import HandlerDocuments
from src.modules.storage.service import LocalStorage, LegacyStorage, StorageLimitExceeded, file_io


class HandlerImages:
    def __init__(self, config: Config):
        self.config = config
        self.created_paths: list[Path] = []
        self.upload_committed = False

    async def convert_to_webp(self, photo: UploadFile, dest: Path) -> Path:
        # Only the suffix is interpreted; client names never become filesystem keys.
        extension = Path((photo.filename or '').replace('\\', '/')).suffix.lower().lstrip('.')
        if extension not in {'jpg', 'jpeg', 'png', 'webp', 'heic', 'heif'}:
            raise InvalidImageFormat('Use a static JPEG, PNG, WebP or HEIC image')
        if not dest.suffix:
            dest = dest / (uuid4().hex + '.webp')
        storage = LocalStorage(self.config.paths)
        key = LegacyStorage(self.config.paths).key(dest)
        try:
            # Private server-created workspace: no caller-controlled ancestors or
            # symlinks are followed by the decoder, including its output file.
            with TemporaryDirectory(prefix='lgg-avatar-') as directory:
                root = Path(directory)
                staging = LocalStorage(SimpleNamespace(media=root))
                result = await staging.put(photo, 'source', max_bytes=self.config.avatar_max_bytes)
                if not result.size:
                    raise InvalidImageFormat('Empty image')
                worker = HandlerDocuments(self.config)
                worker.processing_timeout_seconds = self.config.avatar_processing_timeout_seconds
                await worker.inspect_document(root/'source', extension, root/'normalized.webp', avatar=True)
                async with staging.open('normalized.webp') as stream:
                    class Source:
                        async def read(self, size: int = -1) -> bytes:
                            return await file_io(stream.read, size)
                    # Track before publication: cancellation after link must still
                    # be compensated, subject to durable-reference checks.
                    self.created_paths.append(dest)
                    await storage.put(Source(), key, max_bytes=100 * 1024 * 1024)
            return dest
        except StorageLimitExceeded as exc:
            raise FileTooLarge(f'Avatar exceeds {self.config.avatar_max_bytes / 1024 / 1024:g} MiB upload limit') from exc
        except InvalidDocumentFormat as exc:
            raise InvalidImageFormat('Invalid image: static frame, pixel or processing limit exceeded') from exc
        except ValueError as exc:
            raise InvalidImageFormat('Unsafe avatar storage path') from exc
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                raise InvalidImageFormat('Unsafe avatar storage path') from exc
            raise ImageConversionError('Unable to store avatar safely') from exc
        finally:
            await photo.seek(0)

    async def create_avatar(self) -> Path:
        return self.config.paths.objects / (uuid4().hex + '.webp')
