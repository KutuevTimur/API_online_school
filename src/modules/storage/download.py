"""Authenticated domain endpoints call this only after their access checks."""
import os
import unicodedata
from pathlib import PurePath
from urllib.parse import quote

from fastapi import HTTPException, Request
from starlette.responses import StreamingResponse

from src.modules.storage.service import LegacyStorage, UnsafeStorageKey, file_io


def safe_display_name(name: str | None) -> str:
    name = unicodedata.normalize('NFC', name or 'download').replace('\\', '/').split('/')[-1]
    name = ''.join(c for c in name if c.isprintable() and c not in '\r\n')
    suffix = PurePath(name).suffix
    if len(name) > 200 and 0 < len(suffix) <= 20:
        name = name[:200-len(suffix)] + suffix
    return name[:200] or 'download'


async def private_download(request: Request, raw: str, filename: str,
                           media_type: str = 'application/pdf') -> StreamingResponse:
    if not raw:
        raise HTTPException(404, 'File not available')
    storage = LegacyStorage(request.app.state.config.paths)
    try:
        key = storage.key(raw)
        # Open before responding and keep this exact descriptor through streaming.
        file = await file_io(storage._open, key, cleanup_on_cancel=lambda f: f.close())
    except (OSError, ValueError, UnsafeStorageKey):
        raise HTTPException(404, 'File not available') from None
    try:
        size = (await file_io(os.fstat, file.fileno())).st_size
    except BaseException:
        file.close()
        raise
    start, end, code = 0, size - 1, 200
    headers = {'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff',
               'Accept-Ranges': 'bytes',
               'Content-Disposition': "attachment; filename*=UTF-8''" + quote(safe_display_name(filename), safe='')}
    byte_range = request.headers.get('range')
    if byte_range:
        try:
            unit, value = byte_range.split('=', 1)
            left, right = value.split('-', 1)
            if unit != 'bytes' or ',' in value or (not left and not right):
                raise ValueError()
            if left:
                start = int(left)
                end = min(int(right), size - 1) if right else size - 1
            else:
                length = int(right)
                if length <= 0:
                    raise ValueError()
                start = max(0, size - length)
            if start < 0 or start > end or start >= size:
                raise ValueError()
        except ValueError:
            file.close()
            raise HTTPException(416, 'Invalid range', headers={'Content-Range': f'bytes */{size}'}) from None
        code = 206
        headers['Content-Range'] = f'bytes {start}-{end}/{size}'
    headers['Content-Length'] = str(max(0, end - start + 1))

    async def chunks():
        try:
            await file_io(file.seek, start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = await file_io(file.read, min(64 * 1024, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk
        finally:
            file.close()

    # BackgroundTask also covers a response completed without iterating a body.
    from starlette.background import BackgroundTask
    return StreamingResponse(chunks(), status_code=code, media_type=media_type,
                             headers=headers, background=BackgroundTask(file.close))
