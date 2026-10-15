"""Async storage contract and local implementation with descriptor-relative I/O.

Each component is opened with O_NOFOLLOW: checking resolve() alone would allow
an ancestor symlink to be exchanged between validation and opening the file.
Keys are opaque relative paths, never user supplied filenames or absolute paths.
"""
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import stat
from typing import AsyncIterator, BinaryIO, Protocol, Callable, TypeVar
from uuid import uuid4

from src.core.config.config import PathsConfig


T = TypeVar('T')


async def file_io(call: Callable[..., T], *args, cleanup_on_cancel=None) -> T:
    """Join an in-flight OS operation before closing/reusing its descriptor."""
    task = asyncio.create_task(asyncio.to_thread(call, *args))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        # Repeated cancellation must not orphan a running write/open operation.
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                continue
        if not task.cancelled() and task.exception() is None and cleanup_on_cancel:
            cleanup_on_cancel(task.result())
        raise


class UnsafeStorageKey(ValueError):
    pass


class StorageLimitExceeded(ValueError):
    pass


class ReadableStream(Protocol):
    async def read(self, size: int = -1) -> bytes: ...


@dataclass(frozen=True)
class ObjectStat:
    size: int
    sha256: str | None = None


class Storage(Protocol):
    async def put(self, stream: ReadableStream, key: str, *, max_bytes: int) -> ObjectStat: ...
    def open(self, key: str): ...  # Async context manager yielding BinaryIO.
    async def delete(self, key: str) -> None: ...
    async def stat(self, key: str) -> ObjectStat: ...


class LocalStorage:
    """Immutable files under PathsConfig.media; no external service required."""
    chunk_size = 64 * 1024

    def __init__(self, paths: PathsConfig) -> None:
        self.root = paths.media

    @staticmethod
    def parts(key: str) -> tuple[str, ...]:
        path = PurePosixPath(key)
        if (not key or path.is_absolute() or '\\' in key or '\x00' in key
                or any(p in ('', '.', '..') for p in key.split('/'))):
            raise UnsafeStorageKey('Invalid storage key')
        return path.parts

    def _parent(self, key: str, *, create: bool = False) -> tuple[int, str]:
        parts = self.parts(key)
        fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in parts[:-1]:
                if create:
                    try:
                        os.mkdir(part, mode=0o700, dir_fd=fd)
                    except FileExistsError:
                        pass
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
            return fd, parts[-1]
        except BaseException:
            os.close(fd)
            raise

    def _open(self, key: str) -> BinaryIO:
        parent, name = self._parent(key)
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            try:
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    raise UnsafeStorageKey('Object is not a regular file')
                return os.fdopen(fd, 'rb')
            except BaseException:
                os.close(fd)
                raise
        finally:
            os.close(parent)

    @asynccontextmanager
    async def open(self, key: str) -> AsyncIterator[BinaryIO]:
        file = await file_io(self._open, key, cleanup_on_cancel=lambda f: f.close())
        try:
            yield file
        finally:
            await file_io(file.close)

    async def stat(self, key: str) -> ObjectStat:
        async with self.open(key) as file:
            return ObjectStat((await file_io(os.fstat, file.fileno())).st_size)

    @staticmethod
    def _write_all(file: BinaryIO, chunk: bytes) -> None:
        pending = memoryview(chunk)
        while pending:
            written = file.write(pending)
            if not written:
                raise OSError('Incomplete storage write')
            pending = pending[written:]

    async def put(self, stream: ReadableStream, key: str, *, max_bytes: int) -> ObjectStat:
        if max_bytes < 1:
            raise ValueError('max_bytes must be positive')
        # Keep descriptor acquisition/cleanup synchronous; no cancellation window
        # may leak a descriptor or publish a half-written immutable object.
        parent, name = self._parent(key, create=True)
        temporary = '.upload-' + uuid4().hex
        file = None
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=parent)
            file = os.fdopen(fd, 'wb', buffering=0)
            size = 0
            digest = hashlib.sha256()
            while chunk := await stream.read(self.chunk_size):
                size += len(chunk)
                if size > max_bytes:
                    raise StorageLimitExceeded('File exceeds the byte limit')
                digest.update(chunk)
                # Bounded regular-file writes, moved off the event loop.
                await file_io(self._write_all, file, chunk)
            await file_io(os.fsync, file.fileno())
            file.close()
            file = None
            # link is atomic and refuses overwrite, unlike rename/replace.
            os.link(temporary, name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
            try:
                os.fsync(parent)
            except BaseException:
                os.unlink(name, dir_fd=parent)
                raise
            return ObjectStat(size, digest.hexdigest())
        finally:
            if file is not None:
                file.close()
            try:
                os.unlink(temporary, dir_fd=parent)
            finally:
                os.close(parent)

    def _delete(self, key: str) -> None:
        try:
            parent, name = self._parent(key)
        except FileNotFoundError:
            return
        try:
            try:
                info = os.stat(name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                return
            if not stat.S_ISREG(info.st_mode):
                raise UnsafeStorageKey('Object is not a regular file')
            os.unlink(name, dir_fd=parent)
        finally:
            os.close(parent)

    async def delete(self, key: str) -> None:
        await file_io(self._delete, key)


class LegacyStorage(LocalStorage):
    """Read-only bridge for old DB paths; migration/copying is a separate job."""
    def key(self, raw: str | Path) -> str:
        path = Path(raw)
        # Do not resolve: that would erase evidence of ancestor symlinks.
        try:
            key = str(path.relative_to(self.root))
        except ValueError as exc:
            raise UnsafeStorageKey('Path is outside media') from exc
        self.parts(key)
        return key

    async def put(self, stream: ReadableStream, key: str, *, max_bytes: int) -> ObjectStat:
        raise TypeError('Legacy storage is read-only')

    async def delete(self, key: str) -> None:
        raise TypeError('Legacy storage is read-only')
